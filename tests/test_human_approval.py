import pytest
from backend.database.connection import SessionLocal, init_db
from backend.legal_operations import (
    create_case_for_document,
    start_review,
    submit_review_decision,
    add_comment,
    WorkflowStatus,
    validate_transition
)
from backend.database.models import CaseDB, ReviewDB, CommentDB, AuditLogDB

@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_human_approval_workflow_lifecycle(db_session):
    # 1. Create Case
    case = create_case_for_document(
        db=db_session,
        filename="test_agreement.pdf",
        title="Vendor Contract Review",
        ai_risk_level="HIGH",
        ai_summary="High risk indemnification clause detected.",
        ai_analysis_snapshot="Original AI Findings: Liability uncapped."
    )
    assert case.id is not None
    assert case.status == WorkflowStatus.PENDING_REVIEW.value
    assert case.ai_risk_level == "HIGH"

    # 2. Start Review (PENDING_REVIEW -> UNDER_REVIEW)
    updated_case = start_review(db=db_session, case_id=case.id, reviewer="Counsel John Doe")
    assert updated_case.status == WorkflowStatus.UNDER_REVIEW.value
    assert updated_case.assigned_to == "Counsel John Doe"

    # 3. Submit Review Decision (UNDER_REVIEW -> APPROVED)
    review_record = submit_review_decision(
        db=db_session,
        case_id=case.id,
        decision="APPROVED",
        reviewer="Counsel John Doe",
        reviewer_notes="Approved with liability cap redline clause."
    )
    assert review_record.decision == "APPROVED"
    assert review_record.ai_analysis_snapshot == "Original AI Findings: Liability uncapped."  # Preserved separately
    assert review_record.reviewer_notes == "Approved with liability cap redline clause."
    
    # 4. Verify Case Status updated to APPROVED
    fresh_case = db_session.query(CaseDB).filter(CaseDB.id == case.id).first()
    assert fresh_case.status == "APPROVED"

def test_human_approval_changes_requested_and_rejection(db_session):
    case = create_case_for_document(
        db=db_session,
        filename="service_terms.pdf",
        ai_risk_level="MEDIUM"
    )
    start_review(db=db_session, case_id=case.id, reviewer="Counsel Jane")
    
    # Request Changes (UNDER_REVIEW -> CHANGES_REQUESTED)
    review_req = submit_review_decision(
        db=db_session,
        case_id=case.id,
        decision="CHANGES_REQUESTED",
        reviewer="Counsel Jane",
        reviewer_notes="Payment terms need adjustment from Net 30 to Net 60."
    )
    assert review_req.decision == "CHANGES_REQUESTED"

    # Move back to UNDER_REVIEW
    start_review(db=db_session, case_id=case.id, reviewer="Counsel Jane")
    
    # Reject Case (UNDER_REVIEW -> REJECTED)
    review_rej = submit_review_decision(
        db=db_session,
        case_id=case.id,
        decision="REJECTED",
        reviewer="Counsel Jane",
        reviewer_notes="Unacceptable automatic annual price increase trap."
    )
    assert review_rej.decision == "REJECTED"

def test_invalid_status_transition_rejection(db_session):
    case = create_case_for_document(
        db=db_session,
        filename="draft_contract.pdf"
    )
    # Attempt invalid transition: PENDING_REVIEW -> COMPLETED directly (bypassing review)
    with pytest.raises(ValueError) as exc_info:
        validate_transition(case.status, WorkflowStatus.COMPLETED.value)
    assert "Invalid status transition" in str(exc_info.value)
