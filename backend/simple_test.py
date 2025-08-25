import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing RAG Chatbot Backend...")
print(f"Groq API Key: {'Set' if os.getenv('GROQ_API_KEY') else 'Missing'}")

try:
    from main import app
    print("Main app imported successfully")
    
    import uvicorn
    print("Starting server on http://localhost:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()