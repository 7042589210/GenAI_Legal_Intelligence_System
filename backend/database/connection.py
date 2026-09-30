from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config.settings import DATABASE_URL

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initializes and creates all database tables."""
    from backend.database.models import DocumentDB, ClauseDB, RiskDB, CaseDB, ReviewDB, CommentDB, AuditLogDB
    Base.metadata.create_all(bind=engine)

def get_db():
    """Provides a transactional database session per endpoint request."""
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
