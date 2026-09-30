import asyncio
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from backend.config.settings import LLM_SCAN_MODEL, LLM_REASONING_MODEL, EMBEDDING_MODEL
from backend.ingestion.document_loader import extract_text_from_file_async
from backend.preprocessing.text_normalizer import normalize_legal_text
from backend.clause_analysis import parse_clauses_and_metadata
from backend.vectorstore.chroma_store import build_and_save_vector_store_async
from backend.legal_analysis.risk_analyzer import analyze_contract_risks_async
from backend.legal_operations import (
    create_case_for_document,
    start_review,
    submit_review_decision,
    assign_case,
    update_case_status,
    complete_case,
    close_case,
    WorkflowStatus
)
from backend.database.connection import SessionLocal
from backend.workflows.state import LegalWorkflowState

async def node_ingest_and_parse(state: LegalWorkflowState) -> Dict[str, Any]:
    """Node 1: Ingests document and normalizes raw text."""
    raw = await extract_text_from_file_async(state["file_path"])
    normalized = await asyncio.to_thread(normalize_legal_text, raw)
    return {"raw_text": normalized}

async def node_clause_segmentation(state: LegalWorkflowState) -> Dict[str, Any]:
    """Node 2: Extracts structured clause chunks with metadata."""
    pages_data = [{"text": state["raw_text"], "page": 1}]
    chunks = await asyncio.to_thread(parse_clauses_and_metadata, pages_data, state["filename"])
    return {"structured_chunks": chunks}

async def node_vector_indexing(state: LegalWorkflowState) -> Dict[str, Any]:
    """Node 3: Embeds chunks into ChromaDB using EMBEDDING_MODEL."""
    emb_model = state.get("embedding_model") or EMBEDDING_MODEL
    await build_and_save_vector_store_async(state["structured_chunks"], embedding_model=emb_model)
    return {"status": "INDEXED"}

async def node_ai_risk_analysis(state: LegalWorkflowState) -> Dict[str, Any]:
    """
    Node 4: Evaluates contract risks using RAG reasoning.
    Creates DB case record and initial review.
    """
    answer, docs = await analyze_contract_risks_async()
    
    risk_level = "HIGH" if "HIGH" in answer.upper() else ("MEDIUM" if "MED" in answer.upper() else "LOW")
    
    def save_case():
        db = SessionLocal()
        try:
            case_obj = create_case_for_document(
                db=db,
                filename=state["filename"],
                title=f"Legal Matter: {state['filename']}",
                ai_risk_level=risk_level,
                ai_summary=answer[:500],
                ai_analysis_snapshot=answer
            )
            return case_obj.id
        finally:
            db.close()

    case_id = await asyncio.to_thread(save_case)

    return {
        "case_id": case_id,
        "ai_risk_summary": answer,
        "ai_risk_level": risk_level,
        "status": WorkflowStatus.PENDING_REVIEW.value
    }

def decide_approval_branch(state: LegalWorkflowState) -> str:
    """Conditional Edge: Directs workflow based on human reviewer decision."""
    decision = str(state.get("reviewer_decision") or "").upper()
    if decision == WorkflowStatus.APPROVED.value:
        return "legal_operations"
    elif decision == WorkflowStatus.CHANGES_REQUESTED.value:
        return "request_revisions"
    elif decision == WorkflowStatus.REJECTED.value:
        return "archive_case"
    else:
        return "wait_for_human"

async def node_wait_for_human(state: LegalWorkflowState) -> Dict[str, Any]:
    """Node 5a: Pauses workflow execution awaiting human approval decision."""
    return {"status": WorkflowStatus.PENDING_REVIEW.value}

async def node_request_revisions(state: LegalWorkflowState) -> Dict[str, Any]:
    """Node 5b: Updates status to CHANGES_REQUESTED."""
    def update_db():
        db = SessionLocal()
        try:
            if state.get("case_id"):
                submit_review_decision(
                    db, 
                    state["case_id"], 
                    WorkflowStatus.CHANGES_REQUESTED.value, 
                    reviewer=state.get("reviewer") or "Counsel", 
                    reviewer_notes=state.get("reviewer_notes")
                )
        finally:
            db.close()
    await asyncio.to_thread(update_db)
    return {"status": WorkflowStatus.CHANGES_REQUESTED.value}

async def node_legal_operations(state: LegalWorkflowState) -> Dict[str, Any]:
    """Node 6: Legal Operations execution for APPROVED contracts."""
    def update_db():
        db = SessionLocal()
        try:
            if state.get("case_id"):
                submit_review_decision(
                    db, 
                    state["case_id"], 
                    WorkflowStatus.APPROVED.value, 
                    reviewer=state.get("reviewer") or "Counsel", 
                    reviewer_notes=state.get("reviewer_notes")
                )
                update_case_status(db, state["case_id"], WorkflowStatus.IN_PROGRESS.value)
        finally:
            db.close()
    await asyncio.to_thread(update_db)
    return {"status": WorkflowStatus.IN_PROGRESS.value}

async def node_archive_case(state: LegalWorkflowState) -> Dict[str, Any]:
    """Node 7: Archives REJECTED cases."""
    def update_db():
        db = SessionLocal()
        try:
            if state.get("case_id"):
                close_case(db, state["case_id"])
        finally:
            db.close()
    await asyncio.to_thread(update_db)
    return {"status": WorkflowStatus.CLOSED.value}

def build_legal_workflow_graph() -> StateGraph:
    """
    Constructs the complete LangGraph StateGraph orchestration pipeline.
    """
    graph = StateGraph(LegalWorkflowState)

    # 1. Add Graph Nodes
    graph.add_node("ingest_and_parse", node_ingest_and_parse)
    graph.add_node("clause_segmentation", node_clause_segmentation)
    graph.add_node("vector_indexing", node_vector_indexing)
    graph.add_node("ai_risk_analysis", node_ai_risk_analysis)
    graph.add_node("wait_for_human", node_wait_for_human)
    graph.add_node("request_revisions", node_request_revisions)
    graph.add_node("legal_operations", node_legal_operations)
    graph.add_node("archive_case", node_archive_case)

    # 2. Add Sequential Edges
    graph.set_entry_point("ingest_and_parse")
    graph.add_edge("ingest_and_parse", "clause_segmentation")
    graph.add_edge("clause_segmentation", "vector_indexing")
    graph.add_edge("vector_indexing", "ai_risk_analysis")

    # 3. Add Conditional Edge for Human-in-the-Loop Approval Branching
    graph.add_conditional_edges(
        "ai_risk_analysis",
        decide_approval_branch,
        {
            "legal_operations": "legal_operations",
            "request_revisions": "request_revisions",
            "archive_case": "archive_case",
            "wait_for_human": "wait_for_human"
        }
    )

    graph.add_edge("wait_for_human", END)
    graph.add_edge("request_revisions", END)
    graph.add_edge("legal_operations", END)
    graph.add_edge("archive_case", END)

    return graph.compile()
