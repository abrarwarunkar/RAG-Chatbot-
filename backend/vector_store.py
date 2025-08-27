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
        print(f"Initialized new VectorStore with dimension {self.dimension}")
        
    async def add_documents(self, chunks: List[Dict], doc_id: str, filename: str):
        """Add document chunks to vector store"""
        texts = [chunk["content"] for chunk in chunks]
        print(f"Adding {len(texts)} chunks from {filename}")
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        
        # Normalize embeddings for cosine similarity
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        print(f"Added embeddings to FAISS index. Total documents: {self.index.ntotal}")
        
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
        print(f"Total documents in metadata: {len(self.documents)}")
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        print(f"Searching for: '{query}' in {self.index.ntotal} documents")
        
        if self.index.ntotal == 0:
            print("No documents in vector store")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), min(top_k, self.index.ntotal))
        
        # Return results with scores
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents) and idx >= 0:
                doc = self.documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)
                print(f"Found document: {doc['metadata']['filename']} (chunk {doc['metadata']['chunk_id']}) - Score: {score:.4f}")
        
        # Filter by minimum similarity threshold
        filtered_results = [doc for doc in results if doc["score"] > 0.1]
        print(f"After filtering (score > 0.1): {len(filtered_results)} results")
        
        return filtered_results
    
    def save_index(self, filepath: str):
        """Save vector store to disk"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, f"{filepath}.faiss")
            print(f"Saved FAISS index to {filepath}.faiss")
            
            # Save documents and metadata
            with open(f"{filepath}.pkl", "wb") as f:
                pickle.dump({
                    "documents": self.documents,
                    "embeddings": self.embeddings
                }, f)
            print(f"Saved metadata to {filepath}.pkl")
            
        except Exception as e:
            print(f"Error saving vector store: {e}")
            raise e
    
    def load_index(self, filepath: str):
        """Load vector store from disk"""
        try:
            if os.path.exists(f"{filepath}.faiss") and os.path.exists(f"{filepath}.pkl"):
                # Load FAISS index
                self.index = faiss.read_index(f"{filepath}.faiss")
                print(f"Loaded FAISS index from {filepath}.faiss with {self.index.ntotal} documents")
                
                # Load documents and metadata
                with open(f"{filepath}.pkl", "rb") as f:
                    data = pickle.load(f)
                    self.documents = data["documents"]
                    self.embeddings = data["embeddings"]
                print(f"Loaded {len(self.documents)} document metadata entries")
                
            else:
                print(f"Vector store files not found at {filepath}")
                
        except Exception as e:
            print(f"Error loading vector store: {e}")
            # Reset to empty state on load error
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            self.embeddings = []
            raise e
    
    def clear(self):
        """Clear all documents and reset index"""
        print(f"Clearing vector store. Current size: {self.index.ntotal}")
        
        # Create completely new FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []
        self.embeddings = []
        
        print(f"Cleared vector store. New index has {self.index.ntotal} documents")
    
    def get_status(self):
        """Get current status of vector store"""
        return {
            "total_documents": self.index.ntotal,
            "metadata_count": len(self.documents),
            "embeddings_count": len(self.embeddings),
            "dimension": self.dimension
        }