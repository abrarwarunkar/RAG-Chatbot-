import asyncio
from vector_store_supabase import VectorStoreSupabase
import os
from dotenv import load_dotenv

load_dotenv()

async def test_supabase():
    store = VectorStoreSupabase()
    await store.init()
    
    # Test adding documents
    import uuid
    test_chunks = ["This is a test document about cats.", "Cats are furry animals.", "Dogs are also pets."]
    doc_id = str(uuid.uuid4())
    await store.add_documents(test_chunks, doc_id, "test.txt")
    
    # Test search
    results = await store.search("What are cats?", top_k=3)
    print(f"Search results: {len(results)}")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['content']} (similarity: {result.get('similarity', 'N/A')})")
    
    # Check total chunks
    total = await store.get_total_chunks()
    print(f"Total chunks in database: {total}")

if __name__ == "__main__":
    asyncio.run(test_supabase())