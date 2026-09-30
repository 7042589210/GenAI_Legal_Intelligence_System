from enum import Enum
from typing import Dict, Set

class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"

class CasePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# Centralized status transition rules matrix
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    WorkflowStatus.DRAFT.value: {WorkflowStatus.PENDING_REVIEW.value},
    WorkflowStatus.PENDING_REVIEW.value: {WorkflowStatus.UNDER_REVIEW.value},
    WorkflowStatus.UNDER_REVIEW.value: {
        WorkflowStatus.APPROVED.value,
        WorkflowStatus.REJECTED.value,
        WorkflowStatus.CHANGES_REQUESTED.value
    },
    WorkflowStatus.CHANGES_REQUESTED.value: {WorkflowStatus.UNDER_REVIEW.value},
    WorkflowStatus.APPROVED.value: {WorkflowStatus.IN_PROGRESS.value, WorkflowStatus.COMPLETED.value},
    WorkflowStatus.REJECTED.value: {WorkflowStatus.CLOSED.value, WorkflowStatus.UNDER_REVIEW.value},
    WorkflowStatus.IN_PROGRESS.value: {WorkflowStatus.COMPLETED.value, WorkflowStatus.CLOSED.value},
    WorkflowStatus.COMPLETED.value: {WorkflowStatus.CLOSED.value},
    WorkflowStatus.CLOSED.value: set()  # Terminal state
}

def validate_transition(current_status: str, new_status: str) -> bool:
    """
    Validates whether a workflow status transition is allowed.
    Raises ValueError if the transition is invalid.
    """
    curr = current_status.upper()
    target = new_status.upper()

    if curr not in ALLOWED_TRANSITIONS:
        raise ValueError(f"Unknown status: '{current_status}'")

    if target not in ALLOWED_TRANSITIONS[curr]:
        allowed = ", ".join(sorted(ALLOWED_TRANSITIONS[curr])) or "None (Terminal State)"
        raise ValueError(
            f"Invalid status transition from '{curr}' to '{target}'. "
            f"Allowed next statuses for '{curr}' are: [{allowed}]"
        )
    return True
