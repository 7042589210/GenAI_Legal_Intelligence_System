from backend.clause_analysis.clause_extractor import parse_clauses_and_metadata

def test_parse_clauses_and_metadata(sample_contract_text):
    pages_data = [{"text": sample_contract_text, "page": 1}]
    filename = "test_contract.pdf"
    
    chunks = parse_clauses_and_metadata(pages_data, filename)
    assert len(chunks) > 0
    
    for chunk in chunks:
        assert "text" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["source"] == filename
        assert chunk["metadata"]["page"] == 1
