from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Contract & Clause Schemas ---

class Clause(BaseModel):
    clause_type: str = Field(description="The category of clause, e.g., Limitation of Liability, Termination, Payment Terms", default="Unknown")
    extracted_text: str = Field(description="The verbatim clause text from the contract", default="")
    confidence_score: float = Field(description="Confidence rating between 0.0 and 1.0", default=0.0)

class Citation(BaseModel):
    document_name: str = Field(description="Source document filename")
    page: Optional[int] = Field(description="Page number of the source evidence", default=None)
    clause: str = Field(description="The clause name or title from metadata")
    evidence_text: str = Field(description="The exact snippet of text retrieved as evidence")

class RiskFlag(BaseModel):
    clause: str = Field(description="The clause name or title", default="Unknown")
    clause_number: str = Field(description="The clause section or number, e.g. 8.2", default="")
    clause_type: str = Field(description="The category of clause where risk was detected", default="General")
    severity: str = Field(description="Risk severity level: HIGH, MEDIUM, or LOW", default="MEDIUM")
    rationale: str = Field(description="Explanation of why this term is risky or non-standard", default="")
    potential_impact: str = Field(description="The potential impact of the risk if triggered", default="")
    recommendation: str = Field(description="Action recommended for the reviewer", default="")
    evidence: str = Field(description="Exact excerpt from the text that causes the risk", default="")
    citations: List[Citation] = Field(default_factory=list, description="Verifiable citations from context")

class ContractAnalysisResponse(BaseModel):
    document_summary: str = Field(description="High-level summary of obligations and scope", default="")
    extracted_clauses: List[Clause] = Field(description="List of key extracted clauses", default_factory=list)
    risk_flags: List[RiskFlag] = Field(description="List of identified potential risks", default_factory=list)

# --- Document Summary Schemas ---

class Party(BaseModel):
    name: str = Field(description="Name of the party, e.g., Tata Consultancy Services", default="Unknown")
    role: str = Field(description="Role of the party, e.g., Vendor, Client, Employer", default="Unknown")

class ImportantDate(BaseModel):
    name: str = Field(description="Type of date, e.g., Effective Date, Expiration Date", default="Unknown")
    date: str = Field(description="The extracted date value", default="Unknown")
    evidence_text: str = Field(description="The exact snippet of text retrieved as evidence", default="")
    citations: List[Citation] = Field(default_factory=list, description="Verifiable citations from context")

class KeyClauseSummary(BaseModel):
    clause_number: str = Field(description="The clause section or number, e.g. 8.2", default="")
    clause_title: str = Field(description="Title of the clause, e.g., Termination", default="Unknown")
    summary: str = Field(description="Short 1-3 sentence summary of the clause", default="")
    evidence_text: str = Field(description="The exact snippet of text retrieved as evidence", default="")
    citations: List[Citation] = Field(default_factory=list, description="Verifiable citations from context")

class KeyObligation(BaseModel):
    party: str = Field(description="Party responsible for the obligation", default="Unknown")
    obligation: str = Field(description="The obligation description", default="")
    deadline: str = Field(description="Deadline or frequency, e.g., Annual, 30 days", default="N/A")
    evidence_text: str = Field(description="The exact snippet of text retrieved as evidence", default="")
    citations: List[Citation] = Field(default_factory=list, description="Verifiable citations from context")

class DocumentSummaryResponse(BaseModel):
    document_type: str = Field(description="Type of document, e.g., Vendor Agreement, NDA, Not Determined", default="Unknown")
    executive_summary: str = Field(description="A concise 150-300 word executive summary of the document", default="")
    parties: List[Party] = Field(description="List of parties involved", default_factory=list)
    important_dates: List[ImportantDate] = Field(description="Key dates extracted from the document", default_factory=list)
    key_clauses: List[KeyClauseSummary] = Field(description="Important clauses summarized", default_factory=list)
    obligations: List[KeyObligation] = Field(description="Key obligations extracted", default_factory=list)
    key_takeaways: List[str] = Field(description="4-8 concise bullet points describing important terms", default_factory=list)

# --- Human Approval & Legal Operations Schemas ---

class ReviewDecisionRequest(BaseModel):
    decision: str = Field(description="Review decision: APPROVED, REJECTED, or CHANGES_REQUESTED")
    reviewer: Optional[str] = Field(default="Legal Counsel", description="Name/ID of reviewer")
    reviewer_notes: Optional[str] = Field(default="", description="Comments/feedback from legal reviewer")

class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    reviewer: str
    decision: str
    ai_analysis_snapshot: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CaseCreateRequest(BaseModel):
    filename: str
    title: Optional[str] = None
    ai_risk_level: Optional[str] = "UNKNOWN"
    ai_summary: Optional[str] = None
    priority: Optional[str] = "MEDIUM"

class CaseAssignRequest(BaseModel):
    assigned_to: str = Field(description="Team or counsel assigned to case")

class CaseStatusUpdateRequest(BaseModel):
    status: str = Field(description="New status value, e.g. UNDER_REVIEW, IN_PROGRESS, COMPLETED, CLOSED")

class CasePriorityUpdateRequest(BaseModel):
    priority: str = Field(description="New priority value: LOW, MEDIUM, HIGH, or CRITICAL")

class CommentCreateRequest(BaseModel):
    author: Optional[str] = Field(default="Reviewer", description="Name of commenter")
    comment_text: str = Field(description="Content of the comment")

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    author: str
    comment_text: str
    created_at: datetime

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    action: str
    actor: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime

class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: Optional[int] = None
    title: str
    filename: str
    status: str
    priority: str
    assigned_to: str
    ai_risk_level: str
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    reviews: List[ReviewResponse] = []
    comments: List[CommentResponse] = []
    audit_logs: List[AuditLogResponse] = []
