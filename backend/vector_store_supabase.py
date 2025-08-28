import os
import numpy as np
import uuid
import logging
import psutil
from typing import List, Dict, Any
from supabase import create_client

# Monkey patch to fix httpx proxy issue
import httpx
original_init = httpx.Client.__init__

def patched_init(self, *args, **kwargs):
    # Remove proxy parameter if it exists
    kwargs.pop('proxy', None)
    return original_init(self, *args, **kwargs)

httpx.Client.__init__ = patched_init

logger = logging.getLogger(__name__)

class VectorStoreSupabase:
    def __init__(self):
        # Load Supabase credentials
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY/ANON_KEY not set")

        # Initialize Supabase client (lazy)
        self.client = None
        self.supabase_url = url
        self.supabase_key = key
        
        # Remove heavy sentence-transformer model
        # We'll use the LLM service for embeddings instead
        self.dimension = 384
        self._log_memory_usage("VectorStoreSupabase initialized")

    def _get_client(self):
        """Lazy initialization of Supabase client"""
        if self.client is None:
            # Temporarily disable proxy settings to avoid Supabase client issues
            import os
            old_http_proxy = os.environ.get('HTTP_PROXY')
            old_https_proxy = os.environ.get('HTTPS_PROXY')
            old_http_proxy_lower = os.environ.get('http_proxy')
            old_https_proxy_lower = os.environ.get('https_proxy')

            # Clear proxy environment variables
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                os.environ.pop(key, None)

            try:
                # Create client without proxy interference
                from supabase import Client
                self.client = Client(self.supabase_url, self.supabase_key)
            finally:
                # Restore original proxy settings
                if old_http_proxy:
                    os.environ['HTTP_PROXY'] = old_http_proxy
                if old_https_proxy:
                    os.environ['HTTPS_PROXY'] = old_https_proxy
                if old_http_proxy_lower:
                    os.environ['http_proxy'] = old_http_proxy_lower
                if old_https_proxy_lower:
                    os.environ['https_proxy'] = old_https_proxy_lower

        return self.client

    def _log_memory_usage(self, context: str):
        """Log current memory usage"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.info(f"{context} - Memory usage: {memory_mb:.2f} MB")
        except Exception as e:
            logger.warning(f"Could not log memory usage: {e}")

    async def init(self):
        """Initialize and test Supabase connection."""
        try:
            client = self._get_client()
            # Test connection with minimal query
            resp = client.table("documents").select("id", count="exact").limit(1).execute()
            logger.info("✅ Connected to Supabase via REST API")
            self._log_memory_usage("Supabase connection initialized")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise

    async def clear(self):
        """Clear all documents and chunks with memory optimization."""
        client = self._get_client()
        
        # Clear in smaller batches to avoid memory spikes
        batch_size = 100
        
        # Clear chunks first (child records)
        while True:
            resp = client.table("chunks").delete().limit(batch_size).neq("id", "00000000-0000-0000-0000-000000000000").execute()
            if getattr(resp, "error", None):
                raise RuntimeError(f"Failed to clear chunks: {resp.error}")
            if not resp.data or len(resp.data) < batch_size:
                break
        
        # Clear documents
        while True:
            resp = client.table("documents").delete().limit(batch_size).neq("id", "00000000-0000-0000-0000-000000000000").execute()
            if getattr(resp, "error", None):
                raise RuntimeError(f"Failed to clear documents: {resp.error}")
            if not resp.data or len(resp.data) < batch_size:
                break
                
        logger.info("🧹 Cleared all documents from Supabase")
        self._log_memory_usage("After clearing documents")

    async def add_documents(self, chunks: List[Dict[str, Any]], doc_id: str, filename: str, llm_service=None):
        """Add document + chunks with embeddings using LLM service."""
        client = self._get_client()
        
        # Convert doc_id to string UUID
        doc_uuid = str(uuid.UUID(doc_id)) if isinstance(doc_id, str) else str(doc_id)

        # Insert document
        resp = client.table("documents").insert({"id": doc_uuid, "filename": filename}).execute()
        if getattr(resp, "error", None):
            raise RuntimeError(f"Failed to insert document: {resp.error}")

        # Extract text from chunks with size limiting
        chunk_texts = []
        for chunk in chunks:
            text = chunk.get("content", str(chunk)) if isinstance(chunk, dict) else str(chunk)
            # Limit chunk size to prevent memory issues
            if len(text) > 1000:
                text = text[:1000] + "...[truncated]"
            chunk_texts.append(text)

        # Generate embeddings using LLM service (much lighter)
        if llm_service:
            try:
                # Process in smaller batches to avoid memory spikes
                batch_size = 10
                all_embeddings = []
                
                for i in range(0, len(chunk_texts), batch_size):
                    batch_texts = chunk_texts[i:i + batch_size]
                    batch_embeddings = await llm_service.generate_embeddings(batch_texts)
                    all_embeddings.extend(batch_embeddings)
                    
                    # Log progress
                    self._log_memory_usage(f"Processed {min(i + batch_size, len(chunk_texts))}/{len(chunk_texts)} chunks")
                
                embeddings = np.array(all_embeddings, dtype=np.float32)  # Use float32 to save memory
            except Exception as e:
                logger.warning(f"Failed to generate embeddings with LLM service: {e}")
                # Fallback to simple hash-based embeddings
                embeddings = np.array([self._create_simple_embedding(text) for text in chunk_texts], dtype=np.float32)
        else:
            # Fallback to simple hash-based embeddings
            embeddings = np.array([self._create_simple_embedding(text) for text in chunk_texts], dtype=np.float32)

        # Normalize embeddings (lightweight operation)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        # Insert chunks in smaller batches to avoid memory issues
        BATCH_SIZE = 50  # Reduced from 100
        chunk_rows = []
        
        for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            embedding_list = [float(x) for x in embedding.tolist()]
            chunk_rows.append({
                "document_id": doc_uuid,
                "chunk_index": i,
                "content": chunk_text,
                "embedding": embedding_list
            })

        # Insert in batches with memory monitoring
        for start in range(0, len(chunk_rows), BATCH_SIZE):
            batch = chunk_rows[start:start + BATCH_SIZE]
            resp = client.table("chunks").insert(batch).execute()
            if getattr(resp, "error", None):
                raise RuntimeError(f"Failed to insert chunks batch starting at {start}: {resp.error}")
            
            self._log_memory_usage(f"Inserted batch {start//BATCH_SIZE + 1}/{(len(chunk_rows)-1)//BATCH_SIZE + 1}")

        logger.info(f"📥 Added {len(chunks)} chunks for document {filename}")
        self._log_memory_usage("Document processing complete")

    def _create_simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Create simple hash-based embedding (very lightweight)"""
        import hashlib
        
        embedding = []
        for i in range(dim // 4):
            hash_input = f"{text}_{i}".encode()
            hash_obj = hashlib.md5(hash_input)
            hash_bytes = hash_obj.digest()[:4]
            for byte in hash_bytes:
                embedding.append((byte - 127.5) / 127.5)
        
        while len(embedding) < dim:
            embedding.append(0.0)
        return embedding[:dim]

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Memory-optimized search with streaming processing"""
        client = self._get_client()
        
        # Limit the number of chunks we fetch to prevent memory issues
        MAX_CHUNKS = 1000  # Reasonable limit
        
        resp = client.table("chunks").select("*").limit(MAX_CHUNKS).execute()
        if getattr(resp, "error", None):
            raise RuntimeError(f"Failed to fetch chunks for search: {resp.error}")
        chunks = resp.data or []

        if not chunks:
            return []

        self._log_memory_usage(f"Loaded {len(chunks)} chunks for search")

        # Build document map efficiently
        doc_ids = list(set(c["document_id"] for c in chunks if c.get("document_id")))
        docs_map = {}
        
        if doc_ids:
            # Fetch documents in batches
            batch_size = 100
            for i in range(0, len(doc_ids), batch_size):
                batch_ids = doc_ids[i:i + batch_size]
                docs_resp = client.table("documents").select("id,filename").in_("id", batch_ids).execute()
                if not getattr(docs_resp, "error", None):
                    for d in docs_resp.data or []:
                        docs_map[d["id"]] = d.get("filename", "")

        # Create query embedding using simple hash (very lightweight)
        query_embedding = np.array(self._create_simple_embedding(query), dtype=np.float32)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Process chunks in streaming fashion to save memory
        scored = []
        batch_size = 50
        
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            
            for chunk in batch:
                try:
                    emb = np.array(chunk["embedding"], dtype=np.float32)
                    if emb.size == 0:
                        continue
                    
                    # Fast cosine similarity
                    emb_norm = np.linalg.norm(emb)
                    if emb_norm == 0:
                        similarity = 0.0
                    else:
                        emb = emb / emb_norm
                        similarity = float(np.dot(query_embedding, emb))
                    
                    scored.append({
                        "content": chunk.get("content", ""),
                        "metadata": {
                            "filename": docs_map.get(chunk.get("document_id"), ""),
                            "chunk_id": chunk.get("chunk_index", 0)
                        },
                        "similarity": similarity
                    })
                except Exception as e:
                    logger.warning(f"Error processing chunk: {e}")
                    continue
            
            # Keep only top results to prevent memory growth
            if len(scored) > top_k * 3:
                scored = sorted(scored, key=lambda x: x["similarity"], reverse=True)[:top_k * 2]

        # Final sort and return top_k
        scored_sorted = sorted(scored, key=lambda x: x["similarity"], reverse=True)
        result = scored_sorted[:top_k]
        
        self._log_memory_usage("Search complete")
        return result

    async def get_total_chunks(self):
        """Get total number of chunks efficiently"""
        try:
            client = self._get_client()
            resp = client.table("chunks").select("id", count="exact").limit(1).execute()
            return getattr(resp, "count", len(resp.data or []))
        except Exception as e:
            logger.warning(f"Failed to count chunks: {e}")
            return 0

    # Mock properties for compatibility
    @property
    def index(self):
        class MockIndex:
            def __init__(self, store):
                self.store = store
                self.ntotal = 0
        return MockIndex(self)

    @property
    def documents(self):
        return []

    def save_index(self, path: str):
        pass

    def load_index(self, path: str):
        pass