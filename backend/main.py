from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import uuid
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from document_processor import DocumentProcessor
from vector_store import VectorStore
from llm_service import LLMService

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
doc_processor = DocumentProcessor()
vector_store = VectorStore()

# Vector store path
vector_store_path = "./data/vector_store"
print("Starting with empty vector store")

llm_service = LLMService()

# In-memory session storage (use Redis in production)
sessions: Dict[str, List[Dict]] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    session_id: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/documents/status")
async def get_documents_status():
    """Get status of uploaded documents"""
    return {
        "total_documents": vector_store.index.ntotal,
        "document_count": len(vector_store.documents),
        "documents": [
            {
                "filename": doc["metadata"]["filename"],
                "chunk_id": doc["metadata"]["chunk_id"],
                "content_preview": doc["content"][:100]
            }
            for doc in vector_store.documents
        ]
    }

@app.post("/documents/force-clear")
async def force_clear_all():
    """Force clear everything and restart fresh"""
    global vector_store
    vector_store = VectorStore()  # Create completely new instance
    
    # Remove any saved files
    import shutil
    if os.path.exists("./data"):
        shutil.rmtree("./data")
    
    return {"message": "Force cleared all documents and created new vector store"}

@app.post("/documents/clear")
async def clear_documents():
    """Clear all documents from vector store"""
    try:
        vector_store.clear()
        # Remove saved vector store files
        import shutil
        if os.path.exists(f"{vector_store_path}.faiss"):
            os.remove(f"{vector_store_path}.faiss")
        if os.path.exists(f"{vector_store_path}.pkl"):
            os.remove(f"{vector_store_path}.pkl")
        
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(500, f"Error clearing documents: {str(e)}")

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...), clear_existing: bool = Form(True)):
    """Upload and process documents for RAG"""
    try:
        # Clear existing documents if requested (default behavior)
        if clear_existing:
            print(f"Clearing existing documents. Current count: {vector_store.index.ntotal}")
            vector_store.clear()
            # Also remove saved files
            if os.path.exists(f"{vector_store_path}.faiss"):
                os.remove(f"{vector_store_path}.faiss")
                print("Removed vector_store.faiss")
            if os.path.exists(f"{vector_store_path}.pkl"):
                os.remove(f"{vector_store_path}.pkl")
                print("Removed vector_store.pkl")
            print(f"After clearing: {vector_store.index.ntotal} documents")
        
        processed_docs = []
        
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
                raise HTTPException(400, f"Unsupported file type: {file.filename}")
            
            # Read file content
            content = await file.read()
            
            # Process document
            chunks = await doc_processor.process_document(content, file.filename)
            
            # Store in vector database
            doc_id = str(uuid.uuid4())
            await vector_store.add_documents(chunks, doc_id, file.filename)
            print(f"Added {len(chunks)} chunks from {file.filename}")
            
            processed_docs.append({
                "filename": file.filename,
                "doc_id": doc_id,
                "chunks": len(chunks)
            })
        
        # Save vector store after adding documents
        try:
            vector_store.save_index(vector_store_path)
            print(f"Saved vector store with {vector_store.index.ntotal} documents")
        except Exception as e:
            print(f"Warning: Could not save vector store: {e}")
        
        return {
            "message": f"Successfully processed {len(files)} documents",
            "documents": processed_docs
        }
    
    except Exception as e:
        raise HTTPException(500, f"Error processing documents: {str(e)}")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with streaming response"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Search relevant documents
        relevant_docs = await vector_store.search(request.message, top_k=5)
        
        # Debug: Print what documents are found
        print(f"\n=== DEBUG: Found {len(relevant_docs)} relevant documents ===")
        for i, doc in enumerate(relevant_docs):
            print(f"Doc {i+1}: {doc['metadata']['filename']} - Chunk {doc['metadata']['chunk_id']}")
            print(f"Content preview: {doc['content'][:100]}...")
        print(f"Total documents in vector store: {vector_store.index.ntotal}")
        if len(vector_store.documents) > 0:
            print(f"First document filename: {vector_store.documents[0]['metadata']['filename']}")
        print("=== END DEBUG ===")
        
        # Generate streaming response
        async def generate_response():
            response_text = ""
            sources = []
            
            # Prepare context from retrieved documents
            context = "\n\n".join([doc["content"] for doc in relevant_docs])
            
            if not context.strip():
                # No relevant documents found
                response_text = "I couldn't find relevant information in the uploaded documents to answer your question."
                yield f"data: {json.dumps({'type': 'token', 'content': response_text})}\n\n"
            else:
                # Extract sources
                sources = [
                    {
                        "filename": doc["metadata"]["filename"],
                        "chunk_id": doc["metadata"]["chunk_id"]
                    }
                    for doc in relevant_docs
                ]
                
                # Stream LLM response
                async for token in llm_service.generate_response(request.message, context):
                    response_text += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            # Add to session history
            sessions[session_id].extend([
                {"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": response_text, "sources": sources, "timestamp": datetime.now().isoformat()}
            ])
            
            # Send final message with sources
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'session_id': session_id})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
    except Exception as e:
        raise HTTPException(500, f"Error in chat: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Get chat history for a session"""
    return {"session_id": session_id, "history": sessions.get(session_id, [])}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)