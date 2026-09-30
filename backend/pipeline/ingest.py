"""
Backward compatibility wrapper for ingest module.
"""
from backend.vectorstore.chroma_store import build_and_save_vector_store

__all__ = ["build_and_save_vector_store"]