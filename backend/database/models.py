from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.connection import Base

class DocumentDB(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    clauses = relationship("ClauseDB", back_populates="document", cascade="all, delete-orphan")
    risks = relationship("RiskDB", back_populates="document", cascade="all, delete-orphan")
    cases = relationship("CaseDB", back_populates="document", cascade="all, delete-orphan")

class ClauseDB(Base):
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    clause_type = Column(String)
    extracted_text = Column(Text)
    confidence_score = Column(Float)

    document = relationship("DocumentDB", back_populates="clauses")

class RiskDB(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    clause_type = Column(String)
    severity = Column(String)
    rationale = Column(Text)
    recommendation = Column(Text)

    document = relationship("DocumentDB", back_populates="risks")

# --- Human Approval & Legal Operations Models ---

class CaseDB(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    title = Column(String, index=True)
    filename = Column(String, index=True)
    status = Column(String, default="PENDING_REVIEW", index=True)
    priority = Column(String, default="MEDIUM", index=True)
    assigned_to = Column(String, default="Legal Team")
    ai_risk_level = Column(String, default="UNKNOWN")
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    document = relationship("DocumentDB", back_populates="cases")
    reviews = relationship("ReviewDB", back_populates="case", cascade="all, delete-orphan")
    comments = relationship("CommentDB", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogDB", back_populates="case", cascade="all, delete-orphan")

class ReviewDB(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    reviewer = Column(String, default="Legal Counsel")
    decision = Column(String, default="UNDER_REVIEW")  # APPROVED, REJECTED, CHANGES_REQUESTED, UNDER_REVIEW
    ai_analysis_snapshot = Column(Text, nullable=True)  # Preserves original AI findings separately
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("CaseDB", back_populates="reviews")

class CommentDB(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    author = Column(String, default="Reviewer")
    comment_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseDB", back_populates="comments")

class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    action = Column(String, index=True)  # CASE_CREATED, REVIEW_STARTED, APPROVED, REJECTED, etc.
    actor = Column(String, default="System")
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseDB", back_populates="audit_logs")
