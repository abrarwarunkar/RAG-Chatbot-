import os
import asyncio
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

async def test_groq_api():
    print("Testing Groq API...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found")
        return
    
    print(f"API Key found: {api_key[:10]}...")
    
    try:
        client = AsyncGroq(api_key=api_key)
        
        # Test available models
        print("\nTesting available models...")
        
        # Try different model names
        models_to_test = [
            "llama3-8b-8192",
            "llama3-70b-8192", 
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
        
        for model in models_to_test:
            try:
                print(f"\nTesting model: {model}")
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Hello, can you respond with just 'OK'?"}
                    ],
                    max_tokens=10,
                    temperature=0.1
                )
                
                print(f"SUCCESS {model}: {response.choices[0].message.content}")
                break  # Use the first working model
                
            except Exception as e:
                print(f"FAILED {model}: {str(e)}")
        
    except Exception as e:
        print(f"Error connecting to Groq: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_groq_api())