"""
Comprehensive tests for the BGE embedding pipeline.

Covers:
- Model loading
- Embedding generation and dimension
- Empty / invalid input handling
- Multiple text chunks
- Vector database insertion
- Similarity retrieval
- Semantic legal-text retrieval (end-to-end)
"""
import os
import shutil
import tempfile
import pytest

from backend.embeddings.embedding_service import get_embedding_function
from backend.vectorstore.chroma_store import build_and_save_vector_store, get_vector_store
from backend.config.settings import EMBEDDING_MODEL, EMBEDDING_DIMENSION

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def embedding_fn():
    """Load the BGE embedding function once for the whole module."""
    return get_embedding_function()


@pytest.fixture()
def tmp_chroma_dir():
    """Create a fresh temporary Chroma directory per test, then clean up."""
    d = tempfile.mkdtemp(prefix="test_chroma_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# 1. Model loading
# ---------------------------------------------------------------------------

def test_embedding_function_loads():
    """get_embedding_function() must return a non-None object."""
    emb = get_embedding_function()
    assert emb is not None


def test_embedding_function_loads_explicit_model():
    """Explicit model name must be accepted without raising."""
    emb = get_embedding_function(model_name="BAAI/bge-base-en-v1.5")
    assert emb is not None


# ---------------------------------------------------------------------------
# 2. Embedding generation & dimension
# ---------------------------------------------------------------------------

def test_embedding_dimension_single_text(embedding_fn):
    """Single text must produce a vector of EMBEDDING_DIMENSION (768) dimensions."""
    text = "This agreement is governed by the laws of England and Wales."
    vectors = embedding_fn.embed_documents([text])
    assert len(vectors) == 1
    assert len(vectors[0]) == EMBEDDING_DIMENSION, (
        f"Expected {EMBEDDING_DIMENSION} dims, got {len(vectors[0])}"
    )


def test_embedding_dimension_query(embedding_fn):
    """Query embedding must also be EMBEDDING_DIMENSION dimensions."""
    query = "What are the confidentiality obligations?"
    vector = embedding_fn.embed_query(query)
    assert len(vector) == EMBEDDING_DIMENSION


def test_embedding_values_are_floats(embedding_fn):
    """Embedding values must be numeric floats."""
    vecs = embedding_fn.embed_documents(["Liability is capped at USD 1,000,000."])
    for val in vecs[0]:
        assert isinstance(val, float)


def test_embedding_normalized(embedding_fn):
    """With normalize_embeddings=True, vector magnitude should be approximately 1.0."""
    import math
    vec = embedding_fn.embed_documents(["Indemnification clause."])[0]
    magnitude = math.sqrt(sum(v * v for v in vec))
    assert abs(magnitude - 1.0) < 0.01, f"Expected unit vector, got magnitude={magnitude:.4f}"


# ---------------------------------------------------------------------------
# 3. Empty / invalid input handling
# ---------------------------------------------------------------------------

def test_empty_string_embedding(embedding_fn):
    """Empty string should not raise — returns a vector of correct dimension."""
    vecs = embedding_fn.embed_documents([""])
    assert len(vecs) == 1
    assert len(vecs[0]) == EMBEDDING_DIMENSION


def test_multiple_chunks_embedding(embedding_fn):
    """N input texts must return N embedding vectors of the correct dimension."""
    texts = [
        "Clause 1. Definitions and Interpretation.",
        "Section 2. Limitation of Liability — capped at total contract value.",
        "Clause 3. Either party may terminate with 30 days written notice.",
        "Section 4. Governing Law — England and Wales.",
    ]
    vecs = embedding_fn.embed_documents(texts)
    assert len(vecs) == len(texts)
    for vec in vecs:
        assert len(vec) == EMBEDDING_DIMENSION


# ---------------------------------------------------------------------------
# 4. Vector database insertion
# ---------------------------------------------------------------------------

def test_build_vector_store_creates_store(tmp_chroma_dir):
    """build_and_save_vector_store must return a non-None Chroma store."""
    chunks = [
        {
            "text": "Clause 1. Limitation of Liability: Capped at USD 100,000.",
            "metadata": {"source": "test_contract.pdf", "page": 1, "clause": "Clause 1"},
        }
    ]
    store = build_and_save_vector_store(chunks, chroma_path=tmp_chroma_dir)
    assert store is not None


def test_build_vector_store_persists_data(tmp_chroma_dir):
    """After building, we must be able to reload the store and find documents."""
    chunks = [
        {
            "text": "Section 5. Payment Terms: Net 30 days from invoice date.",
            "metadata": {"source": "test_contract.pdf", "page": 2, "clause": "Section 5"},
        }
    ]
    build_and_save_vector_store(chunks, chroma_path=tmp_chroma_dir)
    # Reload from disk
    reloaded = get_vector_store(chroma_path=tmp_chroma_dir)
    assert reloaded is not None
    results = reloaded.similarity_search("payment terms", k=1)
    assert len(results) >= 1


def test_chunk_metadata_stored(tmp_chroma_dir):
    """Metadata fields (source, page, clause, chunk_id) must be stored in the vector store."""
    chunks = [
        {
            "text": "Clause 7. Intellectual Property: All IP created during this engagement belongs to Tata Group.",
            "metadata": {"source": "ip_agreement.pdf", "page": 3, "clause": "Clause 7"},
        }
    ]
    build_and_save_vector_store(chunks, chroma_path=tmp_chroma_dir)
    store = get_vector_store(chroma_path=tmp_chroma_dir)
    results = store.similarity_search("intellectual property", k=1)
    assert len(results) >= 1
    meta = results[0].metadata
    assert meta.get("source") == "ip_agreement.pdf"
    assert meta.get("page") == 3
    assert "chunk_id" in meta
    assert "embedding_model" in meta


# ---------------------------------------------------------------------------
# 5. Similarity retrieval
# ---------------------------------------------------------------------------

def test_similarity_retrieval_returns_ranked_results(tmp_chroma_dir):
    """Similarity search must return the most relevant chunk first."""
    chunks = [
        {
            "text": "Termination: Either party may terminate the contract by giving 60 days written notice.",
            "metadata": {"source": "termination.pdf", "page": 1, "clause": "Termination"},
        },
        {
            "text": "Payment: The fee shall be USD 500,000 per annum payable quarterly.",
            "metadata": {"source": "payment.pdf", "page": 2, "clause": "Payment"},
        },
        {
            "text": "Confidentiality: Both parties shall maintain strict confidentiality.",
            "metadata": {"source": "confidentiality.pdf", "page": 3, "clause": "Confidentiality"},
        },
    ]
    build_and_save_vector_store(chunks, chroma_path=tmp_chroma_dir)
    store = get_vector_store(chroma_path=tmp_chroma_dir)

    results = store.similarity_search("How can this contract be terminated?", k=1)
    assert len(results) >= 1
    # The termination chunk should be the top result
    top_text = results[0].page_content.lower()
    assert "terminat" in top_text


# ---------------------------------------------------------------------------
# 6. Legal-text semantic retrieval test (per requirements)
# ---------------------------------------------------------------------------

def test_semantic_confidentiality_retrieval(tmp_chroma_dir):
    """
    LEGAL SEMANTIC TEST
    -------------------
    Index: "Either party shall maintain the confidentiality of all proprietary
            information received from the other party."
    Query: "What are the confidentiality obligations?"
    Expected: The confidentiality clause is the top-1 retrieved result.

    NOTE: BGE-base-en-v1.5 is a general-purpose embedding/retrieval model.
    Legal interpretation remains the responsibility of the downstream LLM
    and the human legal reviewer.
    """
    legal_clause = (
        "Either party shall maintain the confidentiality of all proprietary "
        "information received from the other party."
    )
    unrelated_clause = (
        "The Governing Law of this Agreement shall be the laws of England and Wales."
    )

    chunks = [
        {
            "text": legal_clause,
            "metadata": {"source": "nda.pdf", "page": 1, "clause": "Confidentiality"},
        },
        {
            "text": unrelated_clause,
            "metadata": {"source": "nda.pdf", "page": 2, "clause": "Governing Law"},
        },
    ]
    build_and_save_vector_store(chunks, chroma_path=tmp_chroma_dir)
    store = get_vector_store(chroma_path=tmp_chroma_dir)

    query = "What are the confidentiality obligations?"
    results = store.similarity_search(query, k=2)

    assert len(results) >= 1, "Expected at least one result"
    # Top-1 result must contain the confidentiality clause
    top_text = results[0].page_content.lower()
    assert "confidential" in top_text, (
        f"Expected confidentiality clause as top result, got: {results[0].page_content!r}"
    )


# ---------------------------------------------------------------------------
# 7. Configuration sanity
# ---------------------------------------------------------------------------

def test_embedding_model_config():
    """EMBEDDING_MODEL config must point to the BGE model."""
    assert EMBEDDING_MODEL == "BAAI/bge-base-en-v1.5"


def test_embedding_dimension_config():
    """EMBEDDING_DIMENSION must be 768 for bge-base-en-v1.5."""
    assert EMBEDDING_DIMENSION == 768
