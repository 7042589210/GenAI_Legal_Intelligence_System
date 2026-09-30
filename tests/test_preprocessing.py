from backend.preprocessing.text_normalizer import normalize_legal_text

def test_normalize_legal_text():
    raw_text = """
    --- Page 1 (Native) ---
    Clause 1. Definitions and   Interpretation
    Page 1 of 5
    This agreement is entered   into between Tata Consultancy Services
    and CMSS.
    """
    normalized = normalize_legal_text(raw_text)
    
    assert "--- Page 1 (Native) ---" not in normalized
    assert "Page 1 of 5" not in normalized
    assert "Clause 1. Definitions and Interpretation" in normalized
    assert "Tata Consultancy Services and CMSS." in normalized
