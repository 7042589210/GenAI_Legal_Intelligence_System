import pytest
from backend.database.connection import SessionLocal, init_db
from backend.legal_operations import (
    create_case_for_document,
    start_review,
    submit_review_decision,
    assign_case,
    update_case_status,
    update_case_priority,
    complete_case,
    close_case,
    get_dashboard_metrics,
    WorkflowStatus
)
from backend.database.models import CaseDB

@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_legal_operations_lifecycle(db_session):
    # Create and approve case
    case = create_case_for_document(
        db=db_session,
        filename="ops_test_contract.pdf",
        ai_risk_level="LOW"
    )
    start_review(db=db_session, case_id=case.id, reviewer="Legal Ops Lead")
    submit_review_decision(db=db_session, case_id=case.id, decision="APPROVED", reviewer="Legal Ops Lead")

    # 1. Reassign Case
    assigned_case = assign_case(db=db_session, case_id=case.id, assigned_to="Corporate Compliance Team")
    assert assigned_case.assigned_to == "Corporate Compliance Team"

    # 2. Update Priority
    prio_case = update_case_priority(db=db_session, case_id=case.id, priority="CRITICAL")
    assert prio_case.priority == "CRITICAL"

    # 3. Transition to IN_PROGRESS
    status_case = update_case_status(db=db_session, case_id=case.id, new_status=WorkflowStatus.IN_PROGRESS.value)
    assert status_case.status == "IN_PROGRESS"

    # 4. Complete Case
    comp_case = complete_case(db=db_session, case_id=case.id)
    assert comp_case.status == "COMPLETED"
    assert comp_case.completed_at is not None

    # 5. Close Case
    closed_case = close_case(db=db_session, case_id=case.id)
    assert closed_case.status == "CLOSED"
    assert closed_case.closed_at is not None

def test_dashboard_metrics_aggregation(db_session):
    metrics = get_dashboard_metrics(db_session)
    assert "total_cases" in metrics
    assert "status" in metrics
    assert "priority" in metrics
    assert metrics["total_cases"] >= 0
