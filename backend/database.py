"""
Backward compatibility layer for database module.
"""
from backend.database.connection import engine, SessionLocal, Base, get_db, DATABASE_URL

__all__ = ["engine", "SessionLocal", "Base", "get_db", "DATABASE_URL"]