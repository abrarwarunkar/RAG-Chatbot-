import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from vector_store import VectorStore
from document_processor import DocumentProcessor
from llm_service import LLMService

async def debug_rag_system():
    print("=== RAG System Debug ===")
    
    # Initialize components
    vector_store = VectorStore()
    doc_processor = DocumentProcessor()
    llm_service = LLMService()
    
    print(f"1. Vector store initialized with {vector_store.index.ntotal} documents")
    print(f"2. Groq API Key: {'Set' if os.getenv('GROQ_API_KEY') else 'Missing'}")
    
    # Test with sample document
    sample_text = """
    This is a sample document about artificial intelligence.
    AI is transforming many industries including healthcare, finance, and education.
    Machine learning algorithms can process large amounts of data to find patterns.
    Natural language processing helps computers understand human language.
    """
    
    print("\n3. Testing document processing...")
    chunks = await doc_processor.process_document(sample_text.encode(), "sample.txt")
    print(f"   Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"   Chunk {i}: {chunk['content'][:100]}...")
    
    print("\n4. Adding documents to vector store...")
    await vector_store.add_documents(chunks, "test-doc-1", "sample.txt")
    print(f"   Vector store now has {vector_store.index.ntotal} documents")
    
    # Save the vector store
    vector_store.save_index("./data/vector_store")
    print("   Saved vector store to disk")
    
    print("\n5. Testing search functionality...")
    test_queries = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "Tell me about natural language processing",
        "What industries use AI?"
    ]
    
    for query in test_queries:
        print(f"\n   Query: {query}")
        results = await vector_store.search(query, top_k=3)
        print(f"   Found {len(results)} relevant documents")
        
        for j, result in enumerate(results):
            print(f"     Result {j+1}: Score={result['score']:.3f}")
            print(f"     Content: {result['content'][:100]}...")
        
        if results:
            print(f"\n   Testing LLM response...")
            context = "\n\n".join([doc["content"] for doc in results])
            response_tokens = []
            async for token in llm_service.generate_response(query, context):
                response_tokens.append(token)
            response = "".join(response_tokens)
            print(f"   LLM Response: {response[:200]}...")
        else:
            print("   No relevant documents found - this would trigger the fallback message")
    
    print("\n=== Debug Complete ===")
    print(f"Final vector store size: {vector_store.index.ntotal} documents")

if __name__ == "__main__":
    asyncio.run(debug_rag_system())