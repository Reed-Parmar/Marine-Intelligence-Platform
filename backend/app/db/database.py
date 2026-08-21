"""
SQLAlchemy database engine and session management.
Provides clean parameterized execution returning standard Python dictionaries.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import settings

Base = declarative_base()

# Initialize SQLAlchemy engine with connection pool
_engine = None
_SessionFactory = None

if settings.DATABASE_URL:
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    _engine = create_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,
        pool_pre_ping=True
    )
    _SessionFactory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_engine():
    """Returns the SQLAlchemy engine."""
    return _engine


@contextmanager
def get_db() -> Generator[Optional[Session], None, None]:
    """Context manager yielding a SQLAlchemy Session."""
    if _SessionFactory is None:
        raise RuntimeError("Database session factory not initialized. Verify DATABASE_URL is configured.")

    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


def get_db_session() -> Generator[Optional[Session], None, None]:
    """FastAPI dependency for database session."""
    with get_db() as session:
        yield session


def execute_query(query_str: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Executes a SELECT query using SQLAlchemy text() and returns a list of dictionaries.
    Fails explicitly if engine is not configured.
    """
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Verify DATABASE_URL is configured.")
    with _engine.connect() as conn:
        result = conn.execute(text(query_str), params or {})
        return [dict(row) for row in result.mappings()]


def execute_single(query_str: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Executes a SELECT query using SQLAlchemy text() and returns a single row dictionary or None.
    Fails explicitly if engine is not configured.
    """
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Verify DATABASE_URL is configured.")
    with _engine.connect() as conn:
        result = conn.execute(text(query_str), params or {})
        first_row = result.mappings().first()
        return dict(first_row) if first_row else None


def execute_write(query_str: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Executes an INSERT / UPDATE / DELETE query using SQLAlchemy and commits the transaction.
    Returns returning row dictionary if present. Fails explicitly if engine is not configured.
    """
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Verify DATABASE_URL is configured.")
    with _engine.begin() as conn:
        result = conn.execute(text(query_str), params or {})
        if result.returns_rows:
            first_row = result.mappings().first()
            return dict(first_row) if first_row else None
        return None
