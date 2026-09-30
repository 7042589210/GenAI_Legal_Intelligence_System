import logging
import asyncio
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from backend.config.settings import DB_CHROMA_PATH, EMBEDDING_MODEL
from backend.embeddings.embedding_service import get_embedding_function

logger = logging.getLogger(__name__)


def build_and_save_vector_store(
    chunks: List[Dict[str, Any]],
    chroma_path: str = DB_CHROMA_PATH,
    embedding_model: str = None,
) -> Chroma:
    """
    Converts list of chunk dicts into LangChain Document objects, splits them,
    and indexes/persists them in ChromaDB using a local BGE embedding model.

    Each chunk dict must have:
        - "text"     : str   - the document text
        - "metadata" : dict  - must include at minimum "source" and "page";
                               "clause" and "chunk_id" are added automatically.

    Returns the persisted Chroma vector store instance.
    """
    selected_model = embedding_model or EMBEDDING_MODEL
    embeddings = get_embedding_function(model_name=selected_model)

    # Build LangChain Document objects, enriching metadata
    docs = []
    for idx, chunk in enumerate(chunks):
        meta = dict(chunk.get("metadata", {}))
        # Ensure all required metadata fields are present
        meta.setdefault("source", "unknown")
        meta.setdefault("page", 1)
        meta.setdefault("clause", "General Provision")
        meta["chunk_id"] = idx
        meta["embedding_model"] = selected_model
        docs.append(Document(page_content=chunk["text"], metadata=meta))

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)

    logger.info(
        "Building vector store: %d input chunks → %d split docs | model=%s | path=%s",
        len(chunks), len(split_docs), selected_model, chroma_path,
    )

    vector_store = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=chroma_path,
    )

    logger.info("Vector store persisted successfully at '%s'.", chroma_path)
    return vector_store


async def build_and_save_vector_store_async(
    chunks: List[Dict[str, Any]],
    chroma_path: str = DB_CHROMA_PATH,
    embedding_model: str = None,
) -> Chroma:
    """Async wrapper for vector store building."""
    selected_model = embedding_model or EMBEDDING_MODEL
    embeddings = await asyncio.to_thread(get_embedding_function, model_name=selected_model)

    docs = []
    for idx, chunk in enumerate(chunks):
        meta = dict(chunk.get("metadata", {}))
        meta.setdefault("source", "unknown")
        meta.setdefault("page", 1)
        meta.setdefault("clause", "General Provision")
        meta["chunk_id"] = idx
        meta["embedding_model"] = selected_model
        docs.append(Document(page_content=chunk["text"], metadata=meta))

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = await asyncio.to_thread(text_splitter.split_documents, docs)

    logger.info("Building vector store asynchronously...")

    vector_store = await asyncio.to_thread(
        Chroma.from_documents,
        documents=split_docs,
        embedding=embeddings,
        persist_directory=chroma_path,
    )
    
    return vector_store


def get_vector_store(
    chroma_path: str = DB_CHROMA_PATH,
    embedding_model: str = None,
) -> Chroma:
    """
    Loads an existing persisted ChromaDB vector store.
    The embedding model must match the one used when the store was built.
    """
    selected_model = embedding_model or EMBEDDING_MODEL
    embeddings = get_embedding_function(model_name=selected_model)
    return Chroma(
        persist_directory=chroma_path,
        embedding_function=embeddings,
    )
