import os
import shutil
import sys
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from backend.database.connection import get_db, init_db
from backend.schemas import (
    ContractAnalysisResponse,
    CaseResponse,
    CaseCreateRequest,
    ReviewDecisionRequest,
    ReviewResponse,
    CaseAssignRequest,
    CaseStatusUpdateRequest,
    CasePriorityUpdateRequest,
    CommentCreateRequest,
    CommentResponse,
    AuditLogResponse
)
from backend.ingestion.document_loader import extract_text_from_file_async
from backend.clause_analysis import parse_clauses_and_metadata
from backend.vectorstore.chroma_store import build_and_save_vector_store_async
from backend.generation import answer_query
from backend.legal_operations import (
    create_case_for_document,
    start_review,
    submit_review_decision,
    add_comment,
    assign_case,
    update_case_status,
    update_case_priority,
    complete_case,
    close_case,
    get_dashboard_metrics,
    get_all_cases
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Tata Legal AI Intelligence System")

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB tables are initialized on startup
init_db()

@app.get("/")
def read_root():
    return {"status": "Tata Legal AI System API is running with Human Approval & Legal Operations."}

# ==========================================
# 1. AI CONTRACT ANALYSIS & CASE INGESTION
# ==========================================
@app.post("/api/analyze-contract")
async def analyze_contract(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Extract raw text with OCR support
        contract_text = await extract_text_from_file_async(temp_path)
        
        # 2. Extract structured clauses
        pages_data = [{"text": contract_text, "page": 1}]
        structured_chunks = await asyncio.to_thread(parse_clauses_and_metadata, pages_data, file.filename)
        
        # 3. Index into Vector Store
        await build_and_save_vector_store_async(structured_chunks)

        # 4. Automatically create Legal Case for Human Approval Workflow
        def save_case():
            return create_case_for_document(
                db=db,
                filename=file.filename,
                title=f"Legal Review: {file.filename}",
                ai_risk_level="MEDIUM",
                ai_summary=f"Extracted {len(structured_chunks)} clauses from contract.",
                ai_analysis_snapshot=f"Document '{file.filename}' ingested with {len(structured_chunks)} clause chunks indexed in ChromaDB."
            )
        new_case = await asyncio.to_thread(save_case)
        
        return {
            "status": "success",
            "filename": file.filename,
            "extracted_chunks": len(structured_chunks),
            "case_id": new_case.id,
            "case_status": new_case.status
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ==========================================
# 2. HUMAN APPROVAL WORKFLOW ENDPOINTS
# ==========================================
@app.get("/api/cases", response_model=List[CaseResponse])
def list_cases(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetches all legal cases, with optional status filtering."""
    return get_all_cases(db=db, status=status)

@app.get("/api/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Fetches full case details including reviews, comments, and audit trail."""
    from backend.database.models import CaseDB
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found.")
    return case

@app.post("/api/cases/{case_id}/start-review", response_model=CaseResponse)
def api_start_review(case_id: int, reviewer: str = "Legal Counsel", db: Session = Depends(get_db)):
    """Moves case status from PENDING_REVIEW to UNDER_REVIEW."""
    try:
        case = start_review(db=db, case_id=case_id, reviewer=reviewer)
        return case
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/cases/{case_id}/review", response_model=ReviewResponse)
def api_submit_review(case_id: int, req: ReviewDecisionRequest, db: Session = Depends(get_db)):
    """Submits human approval decision (APPROVED, REJECTED, or CHANGES_REQUESTED)."""
    try:
        review_record = submit_review_decision(
            db=db,
            case_id=case_id,
            decision=req.decision,
            reviewer=req.reviewer or "Legal Counsel",
            reviewer_notes=req.reviewer_notes
        )
        return review_record
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/cases/{case_id}/comments", response_model=CommentResponse)
def api_add_comment(case_id: int, req: CommentCreateRequest, db: Session = Depends(get_db)):
    """Adds a reviewer comment to a legal case."""
    try:
        comment = add_comment(db=db, case_id=case_id, author=req.author or "Reviewer", comment_text=req.comment_text)
        return comment
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))

# ==========================================
# 3. LEGAL OPERATIONS & LIFECYCLE ENDPOINTS
# ==========================================
@app.post("/api/cases/{case_id}/assign", response_model=CaseResponse)
def api_assign_case(case_id: int, req: CaseAssignRequest, db: Session = Depends(get_db)):
    """Reassigns case to a specified counsel or operations team."""
    try:
        case = assign_case(db=db, case_id=case_id, assigned_to=req.assigned_to)
        return case
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))

@app.patch("/api/cases/{case_id}/status", response_model=CaseResponse)
def api_update_status(case_id: int, req: CaseStatusUpdateRequest, db: Session = Depends(get_db)):
    """Updates operational status after validating state machine transition rules."""
    try:
        case = update_case_status(db=db, case_id=case_id, new_status=req.status)
        return case
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.patch("/api/cases/{case_id}/priority", response_model=CaseResponse)
def api_update_priority(case_id: int, req: CasePriorityUpdateRequest, db: Session = Depends(get_db)):
    """Updates priority level (LOW, MEDIUM, HIGH, CRITICAL)."""
    try:
        case = update_case_priority(db=db, case_id=case_id, priority=req.priority)
        return case
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/cases/{case_id}/complete", response_model=CaseResponse)
def api_complete_case(case_id: int, db: Session = Depends(get_db)):
    """Marks case as COMPLETED."""
    try:
        case = complete_case(db=db, case_id=case_id)
        return case
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/cases/{case_id}/close", response_model=CaseResponse)
def api_close_case(case_id: int, db: Session = Depends(get_db)):
    """Marks case as CLOSED (archived)."""
    try:
        case = close_case(db=db, case_id=case_id)
        return case
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.get("/api/operations/dashboard-metrics")
def api_dashboard_metrics(db: Session = Depends(get_db)):
    """Returns aggregated status and priority counts for operations dashboard."""
    return get_dashboard_metrics(db=db)