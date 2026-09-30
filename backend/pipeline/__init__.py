"""
Pipeline facade package providing backward compatibility.
"""
from backend.ingestion.document_loader import extract_text_from_file
from backend.preprocessing.text_normalizer import normalize_legal_text
from backend.clause_analysis.clause_extractor import parse_clauses_and_metadata
from backend.vectorstore.chroma_store import build_and_save_vector_store
from backend.generation.answer_generator import answer_query, load_rag_chain
from backend.legal_analysis.risk_analyzer import analyze_contract_risks, load_risk_chain
from backend.legal_analysis.structured_analyzer import analyze_structured_risks

__all__ = [
    "extract_text_from_file",
    "normalize_legal_text",
    "parse_clauses_and_metadata",
    "build_and_save_vector_store",
    "answer_query",
    "load_rag_chain",
    "analyze_contract_risks",
    "load_risk_chain",
    "analyze_structured_risks"
]
