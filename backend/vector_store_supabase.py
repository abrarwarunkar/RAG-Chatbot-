import os
import numpy as np
import uuid
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from supabase import create_client


class VectorStoreSupabase:
    def __init__(self):
        # Load Supabase credentials
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY/ANON_KEY not set")

        # Initialize Supabase client
        self.client = create_client(url, key)

        # Embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = 384

    async def init(self):
        """Initialize and test Supabase connection."""
        try:
            # Test connection by fetching a simple record count
            resp = self.client.table("documents").select("*", count="exact").limit(1).execute()
            print("✅ Connected to Supabase via REST API")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            raise

    async def clear(self):
        """Clear all documents and chunks."""
        # Delete all rows with a WHERE clause that matches all records
        # Supabase requires WHERE clauses for DELETE operations
        resp = self.client.table("chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        if getattr(resp, "error", None):
            raise RuntimeError(f"Failed to clear chunks: {resp.error}")
        
        resp = self.client.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        if getattr(resp, "error", None):
            raise RuntimeError(f"Failed to clear documents: {resp.error}")
        print("🧹 Cleared all documents from Supabase")

    async def add_documents(self, chunks: List[Dict[str, Any]], doc_id: str, filename: str):
        """Add document + chunks with embeddings."""
        # Convert doc_id to string UUID
        doc_uuid = str(uuid.UUID(doc_id)) if isinstance(doc_id, str) else str(doc_id)

        # Insert document and check response
        resp = self.client.table("documents").insert({"id": doc_uuid, "filename": filename}).execute()
        if getattr(resp, "error", None):
            raise RuntimeError(f"Failed to insert document: {resp.error}")

        # Extract text from chunks
        chunk_texts = [
            chunk.get("content", str(chunk)) if isinstance(chunk, dict) else str(chunk)
            for chunk in chunks
        ]

        # Generate embeddings (numpy array)
        embeddings = self.model.encode(chunk_texts)
        # normalize (avoid zero division)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        # Prepare rows in batches for insertion (avoid huge single inserts)
        BATCH_SIZE = 100
        chunk_rows = []
        for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            # Convert embedding to Python floats (json-serializable)
            embedding_list = [float(x) for x in embedding.tolist()]
            chunk_rows.append({
                "document_id": doc_uuid,
                "chunk_index": i,
                "content": chunk_text,
                "embedding": embedding_list
            })

        # Insert in batches
        for start in range(0, len(chunk_rows), BATCH_SIZE):
            batch = chunk_rows[start:start + BATCH_SIZE]
            resp = self.client.table("chunks").insert(batch).execute()
            if getattr(resp, "error", None):
                raise RuntimeError(f"Failed to insert chunks batch starting at {start}: {resp.error}")

        print(f"📥 Added {len(chunks)} chunks for document {filename}")

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Naive search using cosine similarity in Python (REST API can't run pgvector)."""
        # Fetch all chunks
        resp = self.client.table("chunks").select("*").execute()
        if getattr(resp, "error", None):
            raise RuntimeError(f"Failed to fetch chunks for search: {resp.error}")
        chunks = resp.data or []

        if not chunks:
            return []

        # Build a map of document_id -> filename to include filename in results
        doc_ids = list({c["document_id"] for c in chunks if c.get("document_id")})
        docs_map = {}
        if doc_ids:
            # Query documents for filenames; chunk doc_ids may be many, so fetch all docs once
            docs_resp = self.client.table("documents").select("id,filename").in_("id", doc_ids).execute()
            if getattr(docs_resp, "error", None):
                # Not fatal — fallback to blank filenames
                print(f"Warning: failed to fetch document filenames: {docs_resp.error}")
            else:
                for d in docs_resp.data or []:
                    docs_map[d["id"]] = d.get("filename", "")

        # Embed query and normalize
        query_embedding = self.model.encode([query])[0]
        qnorm = np.linalg.norm(query_embedding)
        if qnorm == 0:
            qnorm = 1.0
        query_embedding = query_embedding / qnorm

        # Compute cosine similarity for each chunk
        scored = []
        for chunk in chunks:
            emb = np.array(chunk["embedding"], dtype=float)
            # if embedding shape mismatch, skip
            if emb.size == 0:
                continue
            denom = np.linalg.norm(emb) * np.linalg.norm(query_embedding)
            if denom == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(query_embedding, emb) / denom)
            scored.append({
                "content": chunk.get("content", ""),
                "metadata": {
                    "filename": docs_map.get(chunk.get("document_id"), ""),
                    "chunk_id": chunk.get("chunk_index", 0)
                },
                "similarity": similarity
            })

        # Sort and return top_k
        scored_sorted = sorted(scored, key=lambda x: x["similarity"], reverse=True)
        return scored_sorted[:top_k]

    async def get_total_chunks(self):
        """Get total number of chunks in database."""
        resp = self.client.table("chunks").select("id", count="exact").execute()
        # supabase-py response may expose count attribute; fall back to length of data
        if getattr(resp, "error", None):
            print(f"Warning: failed to count chunks: {resp.error}")
            return len(resp.data or [])
        total = getattr(resp, "count", None)
        if total is None:
            total = len(resp.data or [])
        return total

    @property
    def index(self):
        """Mock property for compatibility."""
        class MockIndex:
            def __init__(self, store):
                self.store = store
                # set ntotal to the count (non-blocking default 0)
                self.ntotal = 0
        return MockIndex(self)

    @property
    def documents(self):
        """Mock property for compatibility (returns empty list)."""
        return []

    def save_index(self, path: str):
        """No-op (Supabase handles persistence)."""
        pass

    def load_index(self, path: str):
        """No-op (Supabase handles persistence)."""
        pass