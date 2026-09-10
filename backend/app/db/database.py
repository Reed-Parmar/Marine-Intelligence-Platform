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
_init_error: Optional[str] = None

if settings.DATABASE_URL:
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    try:
        _engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
            pool_pre_ping=True
        )
        _SessionFactory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
        _init_error = None
    except Exception as e:
        _engine = None
        _SessionFactory = None
        # Sanitize sensitive credentials from error message
        import re
        sanitized = re.sub(r':([^@/:]+)@', ':***@', str(e))
        _init_error = sanitized


def get_engine():
    """Returns the SQLAlchemy engine."""
    return _engine


def get_db_init_error() -> Optional[str]:
    """Returns the retained database initialization error, if any."""
    return _init_error


@contextmanager
def get_db() -> Generator[Optional[Session], None, None]:
    """Context manager yielding a SQLAlchemy Session."""
    if _SessionFactory is None:
        msg = f"Database session factory not initialized. Verify DATABASE_URL is configured. Cause: {_init_error}" if _init_error else "Database session factory not initialized. Verify DATABASE_URL is configured."
        raise RuntimeError(msg)

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


def execute_write_all(query_str: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Executes an INSERT / UPDATE / DELETE query using SQLAlchemy, commits the transaction,
    and returns all RETURNING rows as a list of dictionaries.
    """
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Verify DATABASE_URL is configured.")
    with _engine.begin() as conn:
        result = conn.execute(text(query_str), params or {})
        if result.returns_rows:
            return [dict(row) for row in result.mappings()]
        return []
