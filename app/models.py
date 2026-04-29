"""Database models using SQLAlchemy ORM"""
import json
from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, Integer, Float, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class Incident(Base):
    """SQLAlchemy ORM model for incidents table"""
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    affected_component: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-serialized list
    recommended_steps: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-serialized list
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    log_text: Mapped[str] = mapped_column(Text, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            "id": self.id,
            "summary": self.summary,
            "root_cause": self.root_cause,
            "affected_component": self.affected_component,
            "severity": self.severity,
            "evidence": json.loads(self.evidence),
            "recommended_steps": json.loads(self.recommended_steps),
            "confidence": self.confidence,
            "created_at": self.created_at,
            "log_text": self.log_text,
        }

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, severity={self.severity}, summary={self.summary[:50]}...)>"


# Database session management
_engine = None
_session_factory = None


def get_engine(database_url: str | None = None):
    """
    Get or create SQLAlchemy engine
    
    Args:
        database_url: Database URL (defaults to DATABASE_URL env var or sqlite)
        
    Returns:
        SQLAlchemy Engine instance
    """
    global _engine
    if _engine is None:
        import os
        url = database_url or os.getenv("DATABASE_URL", "sqlite:///./app.db")
        _engine = create_engine(url, echo=False)
    return _engine


def get_session() -> Session:
    """
    Get a new database session
    
    Returns:
        SQLAlchemy Session instance
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = Session(bind=get_engine())
    return Session(bind=get_engine())


def init_db(database_url: str | None = None):
    """Initialize database tables"""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)