"""
Backward compatibility wrapper for ocr_parser module.
"""
from backend.ingestion.document_loader import extract_text_from_file
from backend.ingestion.ocr_engine import extract_text_from_pdf as _extract_from_pdf, run_tesseract_ocr

__all__ = ["extract_text_from_file", "_extract_from_pdf", "run_tesseract_ocr"]