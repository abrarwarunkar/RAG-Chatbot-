import asyncpg
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import os
import uuid
import ssl


class VectorStoreSupabase:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.pool = None

    async def init(self):
        """Initialize database connection pool with SSL (Supabase requires SSL)."""
        database_url = os.getenv("SUPABASE_DATABASE_URL")
        if not database_url:
            raise ValueError("SUPABASE_DATABASE_URL environment variable not set")

        # Create SSL context for Supabase
        ssl_ctx = ssl.create_default_context(cafile=None)

        try:
            self.pool = await asyncpg.create_pool(
                dsn=database_url,
                ssl=ssl_ctx,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            print("✅ Connected to Supabase database")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase database: {e}")
            raise

    async def clear(self):
        """Clear all documents and chunks"""
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM chunks")
            await conn.execute("DELETE FROM documents")
        print("🧹 Cleared all documents from Supabase")

    async def add_documents(self, chunks: List[Dict[str, Any]], doc_id: str, filename: str):
        """Add document and its chunks with embeddings to Supabase"""
        async with self.pool.acquire() as conn:
            # Insert document (convert string to UUID if needed)
            doc_uuid = uuid.UUID(doc_id) if isinstance(doc_id, str) else doc_id
            await conn.execute(
                "INSERT INTO documents (id, filename) VALUES ($1, $2)",
                doc_uuid, filename
            )

            # Extract content from chunks
            chunk_texts = []
            for chunk in chunks:
                if isinstance(chunk, dict):
                    chunk_texts.append(chunk.get('content', str(chunk)))
                else:
                    chunk_texts.append(str(chunk))

            # Generate embeddings
            embeddings = self.model.encode(chunk_texts)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

            # Insert chunks with embeddings
            for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
                embedding_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
                await conn.execute(
                    """INSERT INTO chunks (document_id, chunk_index, content, embedding) 
                       VALUES ($1, $2, $3, $4)""",
                    doc_uuid, i, chunk_text, embedding_str
                )

            print(f"📥 Added {len(chunks)} chunks for document {filename}")

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks using pgvector cosine similarity"""
        query_embedding = self.model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_vector = '[' + ','.join(map(str, query_embedding.tolist())) + ']'

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT c.content, c.chunk_index, d.filename,
                       1 - (c.embedding <=> $1::vector) as similarity
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                ORDER BY c.embedding <=> $1::vector
                LIMIT $2
                """,
                query_vector, top_k
            )

            return [
                {
                    "content": row["content"],
                    "metadata": {
                        "filename": row["filename"],
                        "chunk_id": row["chunk_index"]
                    },
                    "similarity": float(row["similarity"])
                }
                for row in rows
            ]

    async def get_total_chunks(self):
        """Get total number of chunks in database"""
        if not self.pool:
            return 0
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM chunks")
            return result or 0

    @property
    def index(self):
        """Mock property for compatibility"""
        class MockIndex:
            def __init__(self, store):
                self.store = store
                self.ntotal = 0
        return MockIndex(self)

    @property
    def documents(self):
        """Mock property for compatibility"""
        return []

    def save_index(self, path: str):
        """No-op for compatibility"""
        pass

    def load_index(self, path: str):
        """No-op for compatibility"""
        pass
