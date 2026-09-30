import pytest
from backend.schemas.legal_schemas import Citation, RiskFlag, ContractAnalysisResponse
from backend.legal_analysis.structured_analyzer import analyze_structured_risks
import json

def test_evidence_verification_success(monkeypatch):
    # Mock LLM response where the evidence text actually exists in the chunk
    class MockLLMResponse:
        def invoke(self, prompt):
            return ContractAnalysisResponse(
                document_summary="Mock summary",
                extracted_clauses=[],
                risk_flags=[
                    RiskFlag(
                        clause="Termination",
                        clause_number="8.2",
                        clause_type="Termination",
                        severity="HIGH",
                        rationale="Unilateral termination.",
                        potential_impact="Business disruption.",
                        recommendation="Add a cure period.",
                        evidence="The Company may terminate this Agreement immediately",
                        citations=[
                            Citation(
                                document_name="test.pdf",
                                page=1,
                                clause="Termination",
                                evidence_text="The Company may terminate this Agreement immediately"
                            )
                        ]
                    )
                ]
            )

    # Patch the llm creation inside analyze_structured_risks
    class MockLLM:
        def with_structured_output(self, schema):
            return MockLLMResponse()

    monkeypatch.setattr('legal_analysis.structured_analyzer.ChatGroq', lambda **kwargs: MockLLM())

    mock_chunks = [
        {
            "text": "1. Overview\n\n8.2 The Company may terminate this Agreement immediately if the Supplier fails to comply.",
            "metadata": {"source": "test.pdf", "page": 1, "clause": "Termination"}
        }
    ]

    response = analyze_structured_risks(mock_chunks)
    assert len(response.risk_flags) == 1
    rf = response.risk_flags[0]
    
    # Evidence text matches the chunk, so citation should be retained
    assert len(rf.citations) == 1
    assert rf.citations[0].evidence_text == "The Company may terminate this Agreement immediately"
    assert rf.evidence != "Evidence could not be verified or was hallucinated."

def test_evidence_verification_hallucination_rejected(monkeypatch):
    # Mock LLM response where the evidence text DOES NOT exist in the chunk
    class MockLLMResponse:
        def invoke(self, prompt):
            return ContractAnalysisResponse(
                document_summary="Mock summary",
                extracted_clauses=[],
                risk_flags=[
                    RiskFlag(
                        clause="Termination",
                        clause_number="8.2",
                        clause_type="Termination",
                        severity="HIGH",
                        rationale="Unilateral termination.",
                        potential_impact="Business disruption.",
                        recommendation="Add a cure period.",
                        evidence="The Supplier must pay $1,000,000.",
                        citations=[
                            Citation(
                                document_name="test.pdf",
                                page=99,  # Fake page
                                clause="Termination",
                                evidence_text="The Supplier must pay $1,000,000." # Fake text
                            )
                        ]
                    )
                ]
            )

    class MockLLM:
        def with_structured_output(self, schema):
            return MockLLMResponse()

    monkeypatch.setattr('legal_analysis.structured_analyzer.ChatGroq', lambda **kwargs: MockLLM())

    mock_chunks = [
        {
            "text": "1. Overview\n\n8.2 The Company may terminate this Agreement immediately if the Supplier fails to comply.",
            "metadata": {"source": "test.pdf", "page": 1, "clause": "Termination"}
        }
    ]

    response = analyze_structured_risks(mock_chunks)
    rf = response.risk_flags[0]
    
    # Evidence text DOES NOT match the chunk, so citation should be REMOVED
    assert len(rf.citations) == 0
    assert rf.evidence == "Evidence could not be verified or was hallucinated."

def test_risk_explanation_structure():
    rf = RiskFlag(
        clause="Payment",
        clause_number="4.1",
        clause_type="Payment Terms",
        severity="MEDIUM",
        rationale="Net 90 is too long.",
        potential_impact="Cash flow issues.",
        recommendation="Negotiate Net 30.",
        evidence="Payment shall be made within 90 days.",
        citations=[]
    )
    assert rf.clause == "Payment"
    assert rf.clause_number == "4.1"
    assert rf.potential_impact == "Cash flow issues."
