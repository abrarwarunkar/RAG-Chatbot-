import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import pickle
import os

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.documents = []  # Store document metadata
        self.embeddings = []
        
    async def add_documents(self, chunks: List[Dict], doc_id: str, filename: str):
        """Add document chunks to vector store"""
        texts = [chunk["content"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        
        # Normalize embeddings for cosine similarity
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store document metadata
        for i, chunk in enumerate(chunks):
            self.documents.append({
                "content": chunk["content"],
                "metadata": {
                    **chunk["metadata"],
                    "doc_id": doc_id,
                    "filename": filename,
                    "vector_id": len(self.documents)
                }
            })
        
        self.embeddings.extend(embeddings)
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), min(top_k, self.index.ntotal))
        
        # Return results with scores
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)
        
        # Filter by minimum similarity threshold
        results = [doc for doc in results if doc["score"] > 0.1]
        
        return results
    
    def save_index(self, filepath: str):
        """Save vector store to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.faiss")
        
        # Save documents and metadata
        with open(f"{filepath}.pkl", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "embeddings": self.embeddings
            }, f)
    
    def load_index(self, filepath: str):
        """Load vector store from disk"""
        if os.path.exists(f"{filepath}.faiss") and os.path.exists(f"{filepath}.pkl"):
            # Load FAISS index
            self.index = faiss.read_index(f"{filepath}.faiss")
            
            # Load documents and metadata
            with open(f"{filepath}.pkl", "rb") as f:
                data = pickle.load(f)
                self.documents = data["documents"]
                self.embeddings = data["embeddings"]
    
    def clear(self):
        """Clear all documents and reset index"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []
        self.embeddings = []