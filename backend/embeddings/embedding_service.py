from langchain_huggingface import HuggingFaceEmbeddings
from backend.config.settings import EMBEDDING_MODEL


def get_embedding_function(model_name: str = None) -> HuggingFaceEmbeddings:
    """
    Factory function to initialize and return a local HuggingFaceEmbeddings instance.

    Uses BAAI/bge-base-en-v1.5 by default (768-dimensional vectors).
    The model is downloaded once from Hugging Face Hub and cached locally.
    No API key is required.
    """
    selected_model = model_name or EMBEDDING_MODEL or "BAAI/bge-base-en-v1.5"

    return HuggingFaceEmbeddings(
        model_name=selected_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
        # BGE query instruction improves retrieval precision
    )
