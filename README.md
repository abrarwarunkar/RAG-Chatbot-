# RAG Chatbot

A full-stack Retrieval-Augmented Generation (RAG) chatbot application that allows users to upload documents and chat with them using AI. Built with FastAPI backend and React frontend.

## Features

- 📄 **Document Upload**: Support for PDF, DOCX, and TXT files
- 🔍 **Intelligent Search**: Vector-based document retrieval using FAISS
- 💬 **Streaming Chat**: Real-time AI responses with source citations
- 🎨 **Modern UI**: Clean React interface with Tailwind CSS
- 🔄 **Session Management**: Persistent chat history
- 🚀 **Docker Support**: Easy deployment with Docker Compose

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Services   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Groq LLM)    │
│                 │    │                 │    │                 │
│ - Document UI   │    │ - File Processing│    │ - Text Generation│
│ - Chat Interface│    │ - Vector Store  │    │ - Embeddings    │
│ - Source Display│    │ - Search Engine │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Text embeddings
- **Groq**: LLM API for chat responses
- **PyPDF2**: PDF processing
- **python-docx**: Word document processing

### Frontend
- **React**: UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Axios**: HTTP client

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Groq API key

### 1. Clone Repository
```bash
git clone https://github.com/abrarwarunkar/RAG-Chatbot-.git
cd RAG-Chatbot-
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

## Usage

### Development Mode

1. **Start Backend**:
```bash
cd backend
python main.py
```
Backend runs on: `http://localhost:8000`

2. **Start Frontend**:
```bash
cd frontend
npm start
```
Frontend runs on: `http://localhost:3000`

### Docker Deployment

```bash
docker-compose up --build
```

Access the application at `http://localhost:3000`

## API Endpoints

### Document Management
- `POST /upload` - Upload documents
- `GET /documents/status` - Check uploaded documents
- `POST /documents/force-reset` - Clear all documents

### Chat
- `POST /chat` - Send chat message (streaming response)
- `GET /sessions/{session_id}` - Get chat history

### Health
- `GET /health` - Health check

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key for LLM | Required |
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` |

### Supported File Types
- PDF (`.pdf`)
- Word Documents (`.docx`)
- Text Files (`.txt`)

## How It Works

1. **Document Processing**:
   - Files are uploaded and processed into chunks
   - Text is extracted and split into manageable segments
   - Embeddings are generated using Sentence Transformers
   - Vectors are stored in FAISS index

2. **Chat Flow**:
   - User sends a question
   - System searches for relevant document chunks
   - Context is provided to the LLM
   - AI generates response with source citations
   - Response is streamed back to user

3. **Vector Search**:
   - Uses cosine similarity for document retrieval
   - Configurable similarity threshold
   - Returns top-k most relevant chunks

## Project Structure

```
RAG-Chatbot/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── document_processor.py # Document processing logic
│   ├── vector_store.py      # FAISS vector operations
│   ├── llm_service.py       # Groq LLM integration
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   └── types/          # TypeScript types
│   ├── package.json        # Node dependencies
│   └── Dockerfile         # Frontend container
├── docker-compose.yml      # Multi-container setup
└── README.md              # This file
```

## Development

### Adding New Document Types
1. Update `document_processor.py`
2. Add file type validation in `main.py`
3. Update frontend file picker

### Customizing AI Responses
- Modify prompts in `llm_service.py`
- Adjust chunk size and overlap in `document_processor.py`
- Configure similarity thresholds in `vector_store.py`

## Troubleshooting

### Common Issues

1. **Documents not clearing**: Restart backend server
2. **Upload fails**: Check file size and type
3. **No AI responses**: Verify Groq API key
4. **CORS errors**: Check backend CORS configuration

### Debug Endpoints
- `GET /documents/status` - Check loaded documents
- `POST /documents/force-reset` - Nuclear reset option

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Groq](https://groq.com/) for fast LLM inference
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://reactjs.org/) for the frontend framework

## Support

For support, email warunkarabrar@gmail.com or open an issue on GitHub.
