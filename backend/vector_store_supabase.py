import asyncpg
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import os
import uuid

class VectorStoreSupabase:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.pool = None
        
    async def init(self):
        """Initialize database connection pool"""
        database_url = os.getenv("SUPABASE_DATABASE_URL")
        if not database_url:
            raise ValueError("SUPABASE_DATABASE_URL environment variable not set")
        
        self.pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        print("Connected to Supabase database")
    
    async def clear(self):
        """Clear all documents and chunks"""
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM chunks")
            await conn.execute("DELETE FROM documents")
        print("Cleared all documents from Supabase")
    
    async def add_documents(self, chunks: List[str], doc_id: str, filename: str):
        """Add document and its chunks with embeddings to Supabase"""
        async with self.pool.acquire() as conn:
            # Insert document
            await conn.execute(
                "INSERT INTO documents (id, filename) VALUES ($1, $2)",
                uuid.UUID(doc_id), filename
            )
            
            # Generate embeddings for all chunks
            embeddings = self.model.encode(chunks)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Insert chunks with embeddings
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                await conn.execute(
                    """INSERT INTO chunks (document_id, chunk_index, content, embedding) 
                       VALUES ($1, $2, $3, $4)""",
                    uuid.UUID(doc_id), i, chunk, embedding.tolist()
                )
            
            print(f"Added {len(chunks)} chunks for document {filename}")
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks using pgvector cosine similarity"""
        # Generate and normalize query embedding
        query_embedding = self.model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT c.content, c.chunk_index, d.filename,
                       1 - (c.embedding <=> $1) as similarity
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                ORDER BY c.embedding <=> $1
                LIMIT $2
                """,
                query_embedding.tolist(), top_k
            )
            
            results = []
            for row in rows:
                results.append({
                    "content": row["content"],
                    "metadata": {
                        "filename": row["filename"],
                        "chunk_id": row["chunk_index"]
                    },
                    "similarity": float(row["similarity"])
                })
            
            return results
    
    @property
    def index(self):
        """Mock property for compatibility with existing code"""
        class MockIndex:
            def __init__(self, store):
                self.store = store
            
            @property
            async def ntotal(self):
                if not self.store.pool:
                    return 0
                async with self.store.pool.acquire() as conn:
                    result = await conn.fetchval("SELECT COUNT(*) FROM chunks")
                    return result or 0
        
        return MockIndex(self)
    
    @property
    def documents(self):
        """Mock property for compatibility - returns empty list"""
        return []
    
    def save_index(self, path: str):
        """No-op for compatibility - Supabase handles persistence"""
        pass
    
    def load_index(self, path: str):
        """No-op for compatibility - Supabase handles persistence"""
        pass