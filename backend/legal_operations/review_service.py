from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import CaseDB, ReviewDB, CommentDB
from backend.legal_operations.state_machine import WorkflowStatus, validate_transition
from backend.legal_operations.audit_service import log_audit_event

def create_case_for_document(
    db: Session,
    filename: str,
    title: Optional[str] = None,
    ai_risk_level: str = "UNKNOWN",
    ai_summary: Optional[str] = None,
    ai_analysis_snapshot: Optional[str] = None,
    document_id: Optional[int] = None
) -> CaseDB:
    """
    Creates a new legal case/matter and initial review record upon document analysis.
    """
    case_title = title or f"Legal Review: {filename}"
    
    new_case = CaseDB(
        document_id=document_id,
        title=case_title,
        filename=filename,
        status=WorkflowStatus.PENDING_REVIEW.value,
        priority="HIGH" if "HIGH" in ai_risk_level.upper() else "MEDIUM",
        assigned_to="Legal Team",
        ai_risk_level=ai_risk_level,
        ai_summary=ai_summary
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    # Create initial Review record
    initial_review = ReviewDB(
        case_id=new_case.id,
        reviewer="Pending Assignment",
        decision="PENDING_REVIEW",
        ai_analysis_snapshot=ai_analysis_snapshot,
        reviewer_notes="Awaiting human reviewer action."
    )
    db.add(initial_review)
    db.commit()

    # Log Audit Event
    log_audit_event(
        db=db,
        case_id=new_case.id,
        action="CASE_CREATED",
        actor="AI Pipeline",
        previous_status=None,
        new_status=WorkflowStatus.PENDING_REVIEW.value,
        details=f"Case created for '{filename}' with AI risk level: {ai_risk_level}"
    )
    return new_case

def start_review(db: Session, case_id: int, reviewer: str = "Legal Counsel") -> CaseDB:
    """
    Transitions a case status from PENDING_REVIEW or CHANGES_REQUESTED to UNDER_REVIEW.
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    previous_status = case.status
    validate_transition(previous_status, WorkflowStatus.UNDER_REVIEW.value)

    case.status = WorkflowStatus.UNDER_REVIEW.value
    case.assigned_to = reviewer
    case.updated_at = datetime.utcnow()
    db.commit()

    log_audit_event(
        db=db,
        case_id=case.id,
        action="REVIEW_STARTED",
        actor=reviewer,
        previous_status=previous_status,
        new_status=WorkflowStatus.UNDER_REVIEW.value,
        details=f"Human review started by {reviewer}"
    )
    return case

def submit_review_decision(
    db: Session,
    case_id: int,
    decision: str,
    reviewer: str = "Legal Counsel",
    reviewer_notes: Optional[str] = None
) -> ReviewDB:
    """
    Submits a human approval decision (APPROVED, REJECTED, or CHANGES_REQUESTED).
    Preserves original AI analysis snapshot while storing human decision and comments.
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    dec_upper = decision.upper()
    if dec_upper not in {WorkflowStatus.APPROVED.value, WorkflowStatus.REJECTED.value, WorkflowStatus.CHANGES_REQUESTED.value}:
        raise ValueError(f"Invalid decision: '{decision}'. Must be APPROVED, REJECTED, or CHANGES_REQUESTED.")

    previous_status = case.status
    # Ensure current state allows transitioning to decision status
    validate_transition(previous_status, dec_upper)

    # Create new Review record preserving human override separately from AI snapshot
    existing_review = db.query(ReviewDB).filter(ReviewDB.case_id == case_id).order_by(ReviewDB.created_at.desc()).first()
    ai_snapshot = existing_review.ai_analysis_snapshot if existing_review else None

    review_record = ReviewDB(
        case_id=case_id,
        reviewer=reviewer,
        decision=dec_upper,
        ai_analysis_snapshot=ai_snapshot,
        reviewer_notes=reviewer_notes
    )
    db.add(review_record)

    # Update Case Status
    case.status = dec_upper
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(review_record)

    # Log Audit Event
    log_audit_event(
        db=db,
        case_id=case.id,
        action=f"REVIEW_{dec_upper}",
        actor=reviewer,
        previous_status=previous_status,
        new_status=dec_upper,
        details=f"Human reviewer '{reviewer}' decided: {dec_upper}. Notes: {reviewer_notes or 'None'}"
    )
    return review_record

def add_comment(db: Session, case_id: int, author: str, comment_text: str) -> CommentDB:
    """
    Adds a comment to a case and logs an audit trail event.
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    comment = CommentDB(
        case_id=case_id,
        author=author,
        comment_text=comment_text
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    log_audit_event(
        db=db,
        case_id=case_id,
        action="COMMENT_ADDED",
        actor=author,
        previous_status=case.status,
        new_status=case.status,
        details=f"Comment added by {author}: '{comment_text[:50]}...'"
    )
    return comment
