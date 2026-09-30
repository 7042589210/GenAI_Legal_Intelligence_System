import pytest
from backend.workflows.state import LegalWorkflowState
from backend.workflows.legal_graph import build_legal_workflow_graph, decide_approval_branch
from backend.config.settings import LLM_SCAN_MODEL, LLM_REASONING_MODEL, EMBEDDING_MODEL, GROQ_API_KEY, GOOGLE_API_KEY

def test_model_settings_configuration():
    assert LLM_SCAN_MODEL == "qwen/qwen3.8-27b"
    assert LLM_REASONING_MODEL == "openai/gpt-oss-120b"
    assert EMBEDDING_MODEL == "BAAI/bge-base-en-v1.5"
    assert GOOGLE_API_KEY == "AQ.Ab8RN6J6UEZKDPdvvKsGmjOJqCl3_lROMV_0iNgXK0KmO5EcCw"

def test_langgraph_workflow_graph_compilation():
    graph = build_legal_workflow_graph()
    assert graph is not None

def test_decide_approval_branch_logic():
    state_approved = {"reviewer_decision": "APPROVED"}
    assert decide_approval_branch(state_approved) == "legal_operations"

    state_changes = {"reviewer_decision": "CHANGES_REQUESTED"}
    assert decide_approval_branch(state_changes) == "request_revisions"

    state_rejected = {"reviewer_decision": "REJECTED"}
    assert decide_approval_branch(state_rejected) == "archive_case"

    state_pending = {"reviewer_decision": "PENDING_REVIEW"}
    assert decide_approval_branch(state_pending) == "wait_for_human"
