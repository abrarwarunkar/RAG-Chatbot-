# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows users to upload documents and chat with their content using AI. Built with FastAPI backend and React frontend, powered by Groq's Llama3 model.

## Features

- 📄 **Document Upload**: Support for PDF, DOCX, and TXT files
- 🔍 **Semantic Search**: FAISS vector database for efficient document retrieval
- 💬 **Streaming Chat**: Real-time responses with source citations
- 🧠 **AI-Powered**: Uses Groq's Llama3-8B model for fast inference
- 📱 **Modern UI**: Clean React interface with Tailwind CSS
- 🔄 **Session Management**: Persistent chat history

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Groq API** - Fast LLM inference with Llama3-8B
- **FAISS** - Vector similarity search
- **Sentence Transformers** - Document embeddings
- **Python-multipart** - File upload handling

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Groq API key ([Get one here](https://console.groq.com/))

### 1. Clone Repository
```bash
git clone <repository-url>
cd rag-chatbot
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
CORS_ORIGINS=http://localhost:3000
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

### 4. Run Application
**Terminal 1 (Backend):**
```bash
cd backend
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm start
```

### 5. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

1. **Upload Documents**: Click "Upload Documents" and select PDF, DOCX, or TXT files
2. **Start Chatting**: Ask questions about your uploaded documents
3. **View Sources**: See which document chunks were used to generate responses
4. **Session History**: Your chat history is maintained per session

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload documents |
| POST | `/chat` | Chat with streaming response |
| GET | `/documents/status` | Get document status |
| GET | `/sessions/{session_id}` | Get chat history |

## Configuration

### Environment Variables
```env
GROQ_API_KEY=your_groq_api_key_here
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Supported File Types
- PDF (.pdf)
- Word Documents (.docx)
- Text Files (.txt)

## Docker Deployment

### Using Docker Compose
```bash
docker-compose up --build
```

### Individual Containers
**Backend:**
```bash
cd backend
docker build -t rag-backend .
docker run -p 8000:8000 --env-file .env rag-backend
```

**Frontend:**
```bash
cd frontend
docker build -t rag-frontend .
docker run -p 3000:80 rag-frontend
```

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or use different port
uvicorn main:app --host 0.0.0.0 --port 8001
```

**CORS Errors:**
- Ensure `CORS_ORIGINS` in `.env` matches your frontend URL
- Restart backend after changing CORS settings

**API Key Issues:**
- Verify your Groq API key is valid
- Check `.env` file has correct key format

**Document Upload Fails:**
- Ensure file size is under limits
- Check supported file formats (PDF, DOCX, TXT)

## Development

### Project Structure
```
rag-chatbot/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── llm_service.py       # Groq LLM integration
│   ├── vector_store.py      # FAISS vector database
│   ├── document_processor.py # Document processing
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   └── types/          # TypeScript types
│   └── package.json        # Node dependencies
└── docker-compose.yml      # Docker configuration
```

### Adding New Features
1. Backend changes go in respective service files
2. Frontend components in `src/components/`
3. API calls in `src/services/api.ts`
4. Types in `src/types/index.ts`

## Performance

- **Vector Search**: FAISS provides sub-second search on thousands of documents
- **Streaming**: Real-time response generation with Groq's fast inference
- **Caching**: Vector embeddings are cached for faster subsequent searches

## Security

- API keys stored in environment variables
- CORS protection configured
- File type validation on uploads
- Input sanitization for chat messages

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation at `/docs`
- Open an issue on GitHub