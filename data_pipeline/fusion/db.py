"""
Database helper for Phase 5 — Data Fusion.
Uses the existing Supabase client pattern from data_pipeline.file_handler.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_supabase_client():
    """
    Returns the Supabase client using the existing project pattern.
    Reuses data_pipeline.file_handler.get_supabase_client().
    """
    try:
        from data_pipeline.file_handler import get_supabase_client as _get_client
        return _get_client()
    except ImportError:
        logger.warning("data_pipeline.file_handler not available, trying direct init")
        import os
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
            return None
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception as e:
            logger.warning(f"Failed to create Supabase client: {e}")
            return None


def query_table(
    table_name: str,
    select: str = "*",
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 1000,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Query a Supabase table with optional filters.
    Returns a list of record dicts, or empty list on failure.
    """
    sb = get_supabase_client()
    if not sb:
        logger.warning("No Supabase client available. Returning empty results.")
        return []

    try:
        query = sb.table(table_name).select(select)

        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    # Support operator-style filters: {"depth": {"gte": 10, "lte": 100}}
                    for op, val in value.items():
                        query = getattr(query, op)(key, val)
                else:
                    query = query.eq(key, value)

        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        return result.data if result.data else []

    except Exception as e:
        logger.error(f"Query failed on {table_name}: {e}")
        return []


def count_table(table_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
    """
    Count records in a Supabase table with optional filters.
    """
    sb = get_supabase_client()
    if not sb:
        return 0

    try:
        query = sb.table(table_name).select("id", count="exact")
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        query = getattr(query, op)(key, val)
                else:
                    query = query.eq(key, value)

        result = query.limit(0).execute()
        return result.count if result.count is not None else 0

    except Exception as e:
        logger.error(f"Count failed on {table_name}: {e}")
        return 0
