import gradio as gr
import os
from dotenv import load_dotenv
import tempfile
from backend.document_processor import DocumentProcessor
from backend.vector_store import VectorStore
from backend.llm_service import LLMService

# Load environment variables
load_dotenv()

# Initialize services
doc_processor = DocumentProcessor()
vector_store = VectorStore()
llm_service = LLMService()

async def upload_and_process(files):
    """Process uploaded files"""
    if not files:
        return "No files uploaded"
    
    # Clear the vector store before processing new files
    vector_store.clear()
    
    processed_docs = []
    for file in files:
        try:
            # Read file content
            with open(file.name, 'rb') as f:
                content = f.read()
            
            # Process document
            chunks = await doc_processor.process_document(content, file.name)
            
            # Store in vector database
            doc_id = f"doc_{len(processed_docs)}"
            await vector_store.add_documents(chunks, doc_id, file.name)
            
            processed_docs.append(f"✅ {file.name}: {len(chunks)} chunks")
        except Exception as e:
            processed_docs.append(f"❌ {file.name}: Error - {str(e)}")
    
    return "\n".join(processed_docs)

async def chat_with_docs(message, history):
    """Chat with uploaded documents"""
    if not message.strip():
        return history, ""
    
    try:
        # Search relevant documents
        relevant_docs = await vector_store.search(message, top_k=3)
        
        if not relevant_docs:
            response = "I couldn't find relevant information in the uploaded documents."
        else:
            # Generate response
            context = "\n\n".join([doc["content"] for doc in relevant_docs])
            response = ""
            async for token in llm_service.generate_response(message, context):
                response += token
        
        # Add to history
        history.append([message, response])
        return history, ""
    
    except Exception as e:
        history.append([message, f"Error: {str(e)}"])
        return history, ""

# Create Gradio interface
with gr.Blocks(title="RAG Chatbot", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 RAG Chatbot")
    gr.Markdown("Upload documents and chat with your data using AI!")
    
    with gr.Tab("📄 Upload Documents"):
        file_upload = gr.File(
            file_count="multiple",
            file_types=[".pdf", ".docx", ".txt"],
            label="Upload Documents (PDF, DOCX, TXT)"
        )
        upload_btn = gr.Button("Process Documents", variant="primary")
        upload_output = gr.Textbox(label="Processing Status", lines=5)
        
        upload_btn.click(
            upload_and_process,
            inputs=[file_upload],
            outputs=[upload_output]
        )
    
    with gr.Tab("💬 Chat"):
        chatbot = gr.Chatbot(label="Chat with your documents")
        msg = gr.Textbox(
            label="Ask a question about your documents...",
            placeholder="What are the main topics covered?",
            lines=2
        )
        
        msg.submit(
            chat_with_docs,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )

if __name__ == "__main__":
    demo.launch()