---
title: RAG Chatbot
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.15.0
app_file: app.py
pinned: false
license: mit
---

# RAG Chatbot 🤖

A Retrieval-Augmented Generation (RAG) chatbot that allows users to upload documents and chat with their content using AI.

## Features

- 📄 **Document Upload**: Support for PDF, DOCX, and TXT files
- 🔍 **Semantic Search**: FAISS vector database for efficient document retrieval  
- 💬 **AI Chat**: Powered by Groq's Llama3 model
- 🎨 **Modern UI**: Clean Gradio interface

## Usage

1. **Upload Documents**: Go to the "Upload Documents" tab and select your files
2. **Process**: Click "Process Documents" to analyze your files
3. **Chat**: Switch to the "Chat" tab and ask questions about your documents

## Environment Variables

Set your Groq API key in the Hugging Face Spaces settings:

```
GROQ_API_KEY=your_groq_api_key_here
```

## Tech Stack

- **Gradio** - Web interface
- **Groq API** - LLM inference with Llama3
- **FAISS** - Vector similarity search
- **Sentence Transformers** - Document embeddings