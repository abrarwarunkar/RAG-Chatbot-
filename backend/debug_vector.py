import asyncio
from vector_store import VectorStore
from document_processor import DocumentProcessor

async def debug_vector_search():
    print("=== Vector Search Debug ===")
    
    # Initialize
    vector_store = VectorStore()
    doc_processor = DocumentProcessor()
    
    # Test document
    sample_text = """
    Python is a high-level programming language.
    It is widely used for web development, data science, and machine learning.
    Python has simple syntax and is easy to learn.
    """
    
    print("1. Processing document...")
    chunks = await doc_processor.process_document(sample_text.encode(), "test.txt")
    print(f"   Created {len(chunks)} chunks")
    
    print("2. Adding to vector store...")
    await vector_store.add_documents(chunks, "test-1", "test.txt")
    print(f"   Vector store has {vector_store.index.ntotal} documents")
    
    print("3. Testing searches...")
    test_queries = [
        "What is Python?",
        "Tell me about programming languages",
        "How is Python used?",
        "What is machine learning?"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = await vector_store.search(query, top_k=3)
        print(f"   Found {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"     Result {i+1}: Score={result['score']:.4f}")
            print(f"     Content: {result['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(debug_vector_search())