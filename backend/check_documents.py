from vector_store import VectorStore

def check_uploaded_docs():
    vector_store = VectorStore()
    
    # Try to load existing vector store
    try:
        vector_store.load_index("./data/vector_store")
        print(f"Loaded vector store from disk")
    except Exception as e:
        print(f"Could not load vector store: {e}")
    
    print(f"Total documents in vector store: {vector_store.index.ntotal}")
    print(f"Document metadata count: {len(vector_store.documents)}")
    
    if vector_store.documents:
        print("\nFirst few documents:")
        for i, doc in enumerate(vector_store.documents[:3]):
            print(f"  Doc {i+1}: {doc['content'][:100]}...")
            print(f"    Filename: {doc['metadata'].get('filename', 'Unknown')}")
            print(f"    Chunk ID: {doc['metadata'].get('chunk_id', 'Unknown')}")
    else:
        print("No documents found. You need to upload documents first.")

if __name__ == "__main__":
    check_uploaded_docs()