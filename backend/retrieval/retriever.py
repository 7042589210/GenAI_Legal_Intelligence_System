from backend.vectorstore.chroma_store import get_vector_store

def get_retriever(k: int = 3, embedding_model: str = None):
    """
    Instantiates and returns a vector store retriever for contract similarity search.
    Uses the configured EMBEDDING_MODEL (BAAI/bge-base-en-v1.5) by default.
    """
    db = get_vector_store(embedding_model=embedding_model)
    return db.as_retriever(search_kwargs={"k": k})
