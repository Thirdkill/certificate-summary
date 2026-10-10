"""
Database layer for the Certificate OCR System.

Uses SQLite (via SQLAlchemy) for lightweight, zero-config persistent
storage of extracted certificate data and an audit trail of every
document that has been processed (Bonus Feature: Audit Trail).
"""

import uuid
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./certificates.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Certificate(Base):
    """Stores the structured data extracted from a single certificate."""

    __tablename__ = "certificates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    candidate_name = Column(String, nullable=True)
    certificate_title = Column(String, nullable=True)
    organization_name = Column(String, nullable=True)
    issue_date = Column(String, nullable=True)
    certificate_number = Column(String, nullable=True)
    grade_score = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    language = Column(String, default="eng")
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Bonus Feature: Audit Trail — tracks every processing event."""

    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    action = Column(String, nullable=False)      # e.g. "UPLOAD", "EXTRACT", "DELETE"
    status = Column(String, nullable=False)       # "SUCCESS" or "FAILED"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
