"""
Backward compatibility wrapper for RAG engine module.
"""
from backend.prompts.legal_prompts import custom_prompt_template, risk_prompt_template
from backend.generation.answer_generator import load_rag_chain, answer_query
from backend.legal_analysis.risk_analyzer import load_risk_chain, analyze_contract_risks
from backend.legal_analysis.structured_analyzer import analyze_structured_risks

__all__ = [
    "custom_prompt_template",
    "risk_prompt_template",
    "load_rag_chain",
    "answer_query",
    "load_risk_chain",
    "analyze_contract_risks",
    "analyze_structured_risks"
]
