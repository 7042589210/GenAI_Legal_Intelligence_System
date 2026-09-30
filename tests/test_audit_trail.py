import pytest
from backend.database.connection import SessionLocal, init_db
from backend.legal_operations import (
    create_case_for_document,
    start_review,
    submit_review_decision,
    add_comment,
    assign_case,
    complete_case
)
from backend.database.models import CaseDB, AuditLogDB

@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_immutable_audit_trail_logging(db_session):
    # 1. Create Case -> Audit log: CASE_CREATED
    case = create_case_for_document(
        db=db_session,
        filename="audit_test.pdf",
        ai_risk_level="HIGH"
    )
    
    # 2. Start Review -> Audit log: REVIEW_STARTED
    start_review(db=db_session, case_id=case.id, reviewer="Audit Counsel")

    # 3. Add Comment -> Audit log: COMMENT_ADDED
    add_comment(db=db_session, case_id=case.id, author="Audit Counsel", comment_text="Verifying clause 4 indemnity.")

    # 4. Approve Case -> Audit log: REVIEW_APPROVED
    submit_review_decision(db=db_session, case_id=case.id, decision="APPROVED", reviewer="Audit Counsel", reviewer_notes="Looks good.")

    # Fetch audit logs for case
    audit_logs = db_session.query(AuditLogDB).filter(AuditLogDB.case_id == case.id).order_by(AuditLogDB.id.asc()).all()
    
    actions = [log.action for log in audit_logs]
    assert "CASE_CREATED" in actions
    assert "REVIEW_STARTED" in actions
    assert "COMMENT_ADDED" in actions
    assert "REVIEW_APPROVED" in actions
    
    for log in audit_logs:
        assert log.actor is not None
        assert log.timestamp is not None
