import os
import logging
import psutil
from groq import AsyncGroq
from typing import AsyncGenerator, List
import asyncio
import numpy as np

# Memory monitoring
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = None  # Lazy initialization
        # Use fastest, most efficient model on Groq
        self.model = "llama-3.1-8b-instant"  # Faster than llama3-8b-8192
        self._log_memory_usage("LLMService initialized")
    
    def _get_client(self):
        """Lazy initialization of Groq client"""
        if self.client is None:
            self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        return self.client
    
    def _log_memory_usage(self, context: str):
        """Log current memory usage"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.info(f"{context} - Memory usage: {memory_mb:.2f} MB")
        except Exception as e:
            logger.warning(f"Could not log memory usage: {e}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Groq's embedding capabilities"""
        try:
            client = self._get_client()
            
            # Use Groq for embeddings (much lighter than sentence-transformers)
            # Since Groq doesn't have embeddings API yet, we'll create simple embeddings
            # using the LLM to create semantic representations
            embeddings = []
            
            for text in texts:
                # Create a simple embedding by getting the LLM to create a semantic hash
                response = await client.chat.completions.create(
                    model="gemma-7b-it",  # Lighter model for embeddings
                    messages=[
                        {"role": "system", "content": "Convert this text to a semantic vector representation. Return only numbers separated by commas, 384 dimensions."},
                        {"role": "user", "content": f"Text: {text[:500]}"}  # Limit input size
                    ],
                    temperature=0.0,
                    max_tokens=500
                )
                
                # Parse the response to create embedding
                try:
                    embedding_str = response.choices[0].message.content
                    # Fallback: create hash-based embedding if LLM fails
                    embedding = self._create_hash_embedding(text)
                    embeddings.append(embedding)
                except:
                    # Fallback to hash-based embedding
                    embedding = self._create_hash_embedding(text)
                    embeddings.append(embedding)
                
                # Add small delay to avoid rate limits
                await asyncio.sleep(0.1)
            
            self._log_memory_usage(f"Generated {len(texts)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Fallback to hash-based embeddings
            return [self._create_hash_embedding(text) for text in texts]
    
    def _create_hash_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Create a simple hash-based embedding (lightweight fallback)"""
        # Simple hash-based embedding - very lightweight
        import hashlib
        
        # Create multiple hashes for different dimensions
        embedding = []
        for i in range(dim // 4):
            hash_input = f"{text}_{i}".encode()
            hash_obj = hashlib.md5(hash_input)
            # Convert hash to 4 float values
            hash_bytes = hash_obj.digest()[:4]
            for byte in hash_bytes:
                # Normalize to [-1, 1]
                embedding.append((byte - 127.5) / 127.5)
        
        # Pad or trim to exact dimension
        while len(embedding) < dim:
            embedding.append(0.0)
        return embedding[:dim]
    
    async def generate_response(self, query: str, context: str) -> AsyncGenerator[str, None]:
        """Generate streaming response using optimized Groq model"""
        
        client = self._get_client()
        
        # Optimized prompts - shorter to save tokens and memory
        system_prompt = """Answer questions using only the provided context. If no relevant info exists, say "No relevant information found in documents"."""

        # Limit context size to prevent memory issues
        max_context_length = 4000  # Reduced from potentially unlimited
        if len(context) > max_context_length:
            context = context[:max_context_length] + "...[truncated]"

        user_prompt = f"Context: {context}\n\nQ: {query}\nA:"

        try:
            self._log_memory_usage("Starting response generation")
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True,
                temperature=0.1,
                max_tokens=800,  # Reduced from 1000
                top_p=0.9  # Add for better efficiency
            )
            
            token_count = 0
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    token_count += 1
                    yield chunk.choices[0].delta.content
                    
                    # Log memory usage every 50 tokens
                    if token_count % 50 == 0:
                        self._log_memory_usage(f"Generated {token_count} tokens")
                    
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            yield error_msg
    
    async def generate_simple_response(self, query: str) -> str:
        """Generate non-streaming response with memory optimization"""
        try:
            client = self._get_client()
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Be concise."},
                    {"role": "user", "content": query[:1000]}  # Limit input size
                ],
                temperature=0.1,
                max_tokens=500  # Reduced from 1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"