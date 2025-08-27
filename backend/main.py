from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
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
import shutil

# Load environment variables
load_dotenv()

from document_processor import DocumentProcessor
from vector_store_supabase import VectorStoreSupabase
from llm_service import LLMService

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# ✅ Safe CORS settings (only localhost + your Vercel frontend)
origins = [
    "http://localhost:3000",  # local development
    "https://rag-chatbot-client-seven.vercel.app",  # deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Check Route ---
@app.get("/")
def root():
    return {"status": "Backend is running 🚀"}

# --- State Management ---
@app.on_event("startup")
async def startup_event():
    """Initializes the services on application startup and attaches them to the app state."""
    app.state.doc_processor = DocumentProcessor()
    app.state.vector_store = VectorStoreSupabase()
    app.state.llm_service = LLMService()
    
    # Initialize Supabase connection
    await app.state.vector_store.init()
    
    print("Services initialized with Supabase vector store")

# Vector store path
vector_store_path = "./data/vector_store"

# In-memory session storage (use Redis in production)
sessions: Dict[str, List[Dict]] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@app.post("/upload")
async def upload_documents(request: Request, files: List[UploadFile] = File(...), clear_existing: bool = Form(True)):
    """Upload and process documents for RAG"""
    vector_store: VectorStoreSupabase = request.app.state.vector_store
    doc_processor: DocumentProcessor = request.app.state.doc_processor
    
    try:
        if clear_existing:
            print("Clearing existing documents from Supabase")
            await vector_store.clear()
            print("Cleared all existing documents")
        
        processed_docs = []
        
        for file in files:
            if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
                raise HTTPException(400, f"Unsupported file type: {file.filename}")
            
            content = await file.read()
            chunks = await doc_processor.process_document(content, file.filename)
            
            doc_id = str(uuid.uuid4())
            await vector_store.add_documents(chunks, doc_id, file.filename)
            print(f"Added {len(chunks)} chunks from {file.filename}")
            
            processed_docs.append({
                "filename": file.filename,
                "doc_id": doc_id,
                "chunks": len(chunks)
            })
        
        # Supabase handles persistence automatically
        
        return {
            "message": f"Successfully processed {len(files)} documents",
            "documents": processed_docs
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error processing documents: {str(e)}")

@app.post("/chat")
async def chat_endpoint(chat_request: ChatRequest, request: Request):
    """Chat with streaming response"""
    vector_store: VectorStoreSupabase = request.app.state.vector_store
    llm_service: LLMService = request.app.state.llm_service

    try:
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = []
        
        relevant_docs = await vector_store.search(chat_request.message, top_k=5)
        
        # Debug logging
        print(f"\n=== CHAT DEBUG ===")
        print(f"Total docs in vector store: {vector_store.index.ntotal}")
        print(f"Found {len(relevant_docs)} relevant docs")
        for i, doc in enumerate(relevant_docs):
            print(f"Doc {i+1}: {doc['metadata']['filename']} - {doc['content'][:50]}...")
        print("=== END DEBUG ===")
        
        async def generate_response():
            response_text = ""
            sources = []
            
            context = "\n\n".join([doc["content"] for doc in relevant_docs])
            
            if not context.strip():
                response_text = "I couldn't find relevant information in the uploaded documents to answer your question."
                yield f"data: {json.dumps({'type': 'token', 'content': response_text})}\n\n"
            else:
                sources = [
                    {
                        "filename": doc["metadata"]["filename"],
                        "chunk_id": doc["metadata"]["chunk_id"]
                    }
                    for doc in relevant_docs
                ]
                
                async for token in llm_service.generate_response(chat_request.message, context):
                    response_text += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            sessions[session_id].extend([
                {"role": "user", "content": chat_request.message, "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": response_text, "sources": sources, "timestamp": datetime.now().isoformat()}
            ])
            
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'session_id': session_id})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error in chat: {str(e)}")

@app.get("/documents/status")
async def get_documents_status(request: Request):
    """Get detailed status of uploaded documents"""
    vector_store: VectorStoreSupabase = request.app.state.vector_store
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

@app.post("/documents/force-reset")
async def force_reset_everything(request: Request):
    """Completely reset everything - nuclear option"""
    try:
        vector_store: VectorStoreSupabase = request.app.state.vector_store
        await vector_store.clear()
        
        # Clear sessions
        global sessions
        sessions = {}
        
        return {"message": "Complete reset successful - all data cleared from Supabase"}
    except Exception as e:
        raise HTTPException(500, f"Error during reset: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
