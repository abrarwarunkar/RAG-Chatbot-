import os
from groq import AsyncGroq
from typing import AsyncGenerator
import asyncio

class LLMService:
    def __init__(self):
        self.client = AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = "llama3-8b-8192"
    
    async def generate_response(self, query: str, context: str) -> AsyncGenerator[str, None]:
        """Generate streaming response using Groq Llama3-8B"""
        
        system_prompt = """You are a helpful AI assistant that answers questions based on provided context documents. 

Instructions:
- Use ONLY the information from the provided context to answer questions
- If the context doesn't contain relevant information, say "I couldn't find relevant information in the uploaded documents to answer your question."
- Be concise and accurate
- Cite specific information when possible
- Don't make up information not present in the context"""

        user_prompt = f"""Context from documents:
{context}

Question: {query}

Answer based on the context above:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True,
                temperature=0.1,
                max_tokens=1000
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    async def generate_simple_response(self, query: str) -> str:
        """Generate non-streaming response"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"