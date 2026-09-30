"""
Backward compatibility layer for models and schemas.
"""
from backend.schemas.legal_schemas import Clause, RiskFlag, ContractAnalysisResponse
from backend.database.models import DocumentDB, ClauseDB, RiskDB

__all__ = [
    "Clause",
    "RiskFlag",
    "ContractAnalysisResponse",
    "DocumentDB",
    "ClauseDB",
    "RiskDB"
]