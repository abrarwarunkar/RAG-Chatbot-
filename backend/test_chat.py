import asyncio
import json
from main import app
from fastapi.testclient import TestClient

def test_chat_endpoint():
    print("Testing chat endpoint...")
    
    client = TestClient(app)
    
    # Test the documents status first
    print("\n1. Checking document status...")
    response = client.get("/documents/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test chat with a simple question
    print("\n2. Testing chat...")
    chat_request = {
        "message": "What is artificial intelligence?",
        "session_id": "test-session"
    }
    
    response = client.post("/chat", json=chat_request)
    print(f"Chat Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Chat response received (streaming):")
        # For streaming response, we'll just check if it starts correctly
        content = response.content.decode()
        print(f"First 200 chars: {content[:200]}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_chat_endpoint()