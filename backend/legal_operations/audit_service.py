from typing import Optional
from sqlalchemy.orm import Session
from backend.database.models import AuditLogDB

def log_audit_event(
    db: Session,
    case_id: int,
    action: str,
    actor: str = "System",
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
    details: Optional[str] = None
) -> AuditLogDB:
    """
    Creates an immutable audit trail entry for a legal case/review action.
    """
    audit_entry = AuditLogDB(
        case_id=case_id,
        action=action.upper(),
        actor=actor,
        previous_status=previous_status,
        new_status=new_status,
        details=details
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry
