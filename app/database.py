"""Database connection and session management"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


# Database URL from environment, defaulting to sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./incidents.db")

# Create engine with special settings for SQLite
if DATABASE_URL.startswith("sqlite"):
    # SQLite needs check_same_thread=False for FastAPI compatibility
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy session for database operations
        
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialize database tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)