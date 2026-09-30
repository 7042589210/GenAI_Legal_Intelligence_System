"""
Backward compatibility wrapper for clause_extractor module.
"""
from backend.preprocessing.text_normalizer import normalize_legal_text
from backend.clause_analysis.clause_extractor import parse_clauses_and_metadata

__all__ = ["normalize_legal_text", "parse_clauses_and_metadata"]
