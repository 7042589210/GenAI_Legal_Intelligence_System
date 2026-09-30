from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.models import CaseDB, ReviewDB, CommentDB, AuditLogDB
from backend.legal_operations.state_machine import WorkflowStatus, CasePriority, validate_transition
from backend.legal_operations.audit_service import log_audit_event

def assign_case(db: Session, case_id: int, assigned_to: str, actor: str = "Admin") -> CaseDB:
    """
    Assigns a legal case to a reviewer or legal operations counsel.
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    old_assignee = case.assigned_to
    case.assigned_to = assigned_to
    case.updated_at = datetime.utcnow()
    db.commit()

    log_audit_event(
        db=db,
        case_id=case_id,
        action="CASE_ASSIGNED",
        actor=actor,
        previous_status=case.status,
        new_status=case.status,
        details=f"Case reassigned from '{old_assignee}' to '{assigned_to}'"
    )
    return case

def update_case_status(db: Session, case_id: int, new_status: str, actor: str = "Legal Ops") -> CaseDB:
    """
    Updates operational case status after validating state transitions.
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    previous_status = case.status
    validate_transition(previous_status, new_status)

    case.status = new_status.upper()
    case.updated_at = datetime.utcnow()
    db.commit()

    log_audit_event(
        db=db,
        case_id=case_id,
        action="STATUS_UPDATED",
        actor=actor,
        previous_status=previous_status,
        new_status=new_status.upper(),
        details=f"Operational status updated from '{previous_status}' to '{new_status.upper()}'"
    )
    return case

def update_case_priority(db: Session, case_id: int, priority: str, actor: str = "Legal Ops") -> CaseDB:
    """
    Updates priority level (LOW, MEDIUM, HIGH, CRITICAL) for a case.
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    prio_upper = priority.upper()
    if prio_upper not in [p.value for p in CasePriority]:
        raise ValueError(f"Invalid priority: '{priority}'. Must be LOW, MEDIUM, HIGH, or CRITICAL.")

    old_priority = case.priority
    case.priority = prio_upper
    case.updated_at = datetime.utcnow()
    db.commit()

    log_audit_event(
        db=db,
        case_id=case_id,
        action="PRIORITY_UPDATED",
        actor=actor,
        previous_status=case.status,
        new_status=case.status,
        details=f"Priority updated from '{old_priority}' to '{prio_upper}'"
    )
    return case

def complete_case(db: Session, case_id: int, actor: str = "Legal Ops") -> CaseDB:
    """
    Marks a legal case as COMPLETED after verification.
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    previous_status = case.status
    validate_transition(previous_status, WorkflowStatus.COMPLETED.value)

    case.status = WorkflowStatus.COMPLETED.value
    case.completed_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    db.commit()

    log_audit_event(
        db=db,
        case_id=case_id,
        action="CASE_COMPLETED",
        actor=actor,
        previous_status=previous_status,
        new_status=WorkflowStatus.COMPLETED.value,
        details="Legal Operations case marked as COMPLETED"
    )
    return case

def close_case(db: Session, case_id: int, actor: str = "Legal Ops") -> CaseDB:
    """
    Marks a legal case as CLOSED (terminal state).
    """
    case = db.query(CaseDB).filter(CaseDB.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    previous_status = case.status
    validate_transition(previous_status, WorkflowStatus.CLOSED.value)

    case.status = WorkflowStatus.CLOSED.value
    case.closed_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    db.commit()

    log_audit_event(
        db=db,
        case_id=case_id,
        action="CASE_CLOSED",
        actor=actor,
        previous_status=previous_status,
        new_status=WorkflowStatus.CLOSED.value,
        details="Legal Operations case CLOSED and archived"
    )
    return case

def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Aggregates status and priority metric counts for Legal Operations dashboard.
    """
    status_counts = db.query(CaseDB.status, func.count(CaseDB.id)).group_by(CaseDB.status).all()
    priority_counts = db.query(CaseDB.priority, func.count(CaseDB.id)).group_by(CaseDB.priority).all()

    metrics = {
        "status": {s.value: 0 for s in WorkflowStatus},
        "priority": {p.value: 0 for p in CasePriority},
        "total_cases": db.query(func.count(CaseDB.id)).scalar() or 0
    }

    for status, count in status_counts:
        metrics["status"][status] = count

    for priority, count in priority_counts:
        metrics["priority"][priority] = count

    return metrics

def get_all_cases(db: Session, status: Optional[str] = None) -> List[CaseDB]:
    """
    Fetches all legal cases with optional status filtering.
    """
    query = db.query(CaseDB)
    if status:
        query = query.filter(CaseDB.status == status.upper())
    return query.order_by(CaseDB.updated_at.desc()).all()
