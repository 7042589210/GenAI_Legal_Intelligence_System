from typing import TypedDict, List, Dict, Any, Optional
from backend.config.settings import LLM_SCAN_MODEL, LLM_REASONING_MODEL, EMBEDDING_MODEL

class LegalWorkflowState(TypedDict):
    """State schema for the LangGraph Legal Workflow Engine."""
    file_path: str
    filename: str
    raw_text: Optional[str]
    structured_chunks: List[Dict[str, Any]]
    ai_risk_summary: Optional[str]
    ai_risk_level: Optional[str]
    case_id: Optional[int]
    status: str
    priority: str
    assigned_to: str
    reviewer: Optional[str]
    reviewer_decision: Optional[str]
    reviewer_notes: Optional[str]
    audit_logs: List[Dict[str, Any]]
    llm_scan_model: str
    llm_reasoning_model: str
    embedding_model: str
