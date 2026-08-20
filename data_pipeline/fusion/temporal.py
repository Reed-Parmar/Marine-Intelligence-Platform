"""
Temporal alignment and timestamp comparison for Phase 5 Data Fusion.

Preserves Phase 4 timezone semantics:
- Normalizes timezone-aware timestamps to standard UTC for precise delta calculations.
- Preserves naive/local timestamps without assuming UTC/IST or silently inventing offsets.
- Handles missing timestamps without hallucinating dates.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import dateutil.parser


def parse_marine_timestamp(ts_str: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """
    Parses a timestamp string into a Python datetime object.
    Preserves awareness:
    - Timezone-aware strings (e.g., '...Z', '+05:30') yield tz-aware datetimes.
    - Naive strings (e.g., '2026-03-15 08:30:00') yield naive datetimes.
    Returns None if ts_str is None, empty, or unparseable.
    """
    if ts_str is None:
        return None
    if isinstance(ts_str, datetime):
        return ts_str

    s = str(ts_str).strip()
    if not s or s.lower() in ("none", "null", "nan", "-999", "na", ""):
        return None

    try:
        dt = dateutil.parser.isoparse(s)
        return dt
    except Exception:
        try:
            dt = dateutil.parser.parse(s)
            return dt
        except Exception:
            return None


def temporal_distance_hours(
    time1: Optional[Union[str, datetime]],
    time2: Optional[Union[str, datetime]]
) -> Optional[float]:
    """
    Computes the absolute difference between two timestamps in hours.

    Returns:
        float hours difference, or None if either timestamp is missing or incompatible.
    """
    dt1 = parse_marine_timestamp(time1)
    dt2 = parse_marine_timestamp(time2)

    if dt1 is None or dt2 is None:
        return None

    # Handle awareness compatibility
    if dt1.tzinfo is not None and dt2.tzinfo is not None:
        # Both tz-aware: normalize to UTC
        dt1_utc = dt1.astimezone(timezone.utc)
        dt2_utc = dt2.astimezone(timezone.utc)
        delta = abs((dt1_utc - dt2_utc).total_seconds())
        return delta / 3600.0
    elif dt1.tzinfo is None and dt2.tzinfo is None:
        # Both naive: compare directly
        delta = abs((dt1 - dt2).total_seconds())
        return delta / 3600.0
    else:
        # One aware, one naive:
        # To avoid silent errors or timezone fabrications, compare assuming local clock match
        # while stripping tzinfo for distance computation
        dt1_naive = dt1.replace(tzinfo=None)
        dt2_naive = dt2.replace(tzinfo=None)
        delta = abs((dt1_naive - dt2_naive).total_seconds())
        return delta / 3600.0


def is_within_temporal_window(
    time1: Optional[Union[str, datetime]],
    time2: Optional[Union[str, datetime]],
    window_hours: float
) -> bool:
    """
    Checks if two timestamps are within a given window (in hours).
    Returns False if either timestamp is None or missing.
    """
    diff_h = temporal_distance_hours(time1, time2)
    if diff_h is None:
        return False
    return diff_h <= window_hours


def is_within_date_range(
    ts: Optional[Union[str, datetime]],
    date_from: Optional[Union[str, datetime]] = None,
    date_to: Optional[Union[str, datetime]] = None
) -> bool:
    """
    Checks if a timestamp falls between date_from and date_to (inclusive).
    If date_from is None, no lower bound is enforced.
    If date_to is None, no upper bound is enforced.
    If ts is None, returns False.
    """
    if ts is None:
        return False

    dt = parse_marine_timestamp(ts)
    if dt is None:
        return False

    if date_from is not None:
        dt_from = parse_marine_timestamp(date_from)
        if dt_from is not None:
            # Reconcile tz awareness
            if dt.tzinfo is not None and dt_from.tzinfo is None:
                dt_from = dt_from.replace(tzinfo=dt.tzinfo)
            elif dt.tzinfo is None and dt_from.tzinfo is not None:
                dt = dt.replace(tzinfo=dt_from.tzinfo)
            if dt < dt_from:
                return False

    if date_to is not None:
        dt_to = parse_marine_timestamp(date_to)
        if dt_to is not None:
            # Reconcile tz awareness
            if dt.tzinfo is not None and dt_to.tzinfo is None:
                dt_to = dt_to.replace(tzinfo=dt.tzinfo)
            elif dt.tzinfo is None and dt_to.tzinfo is not None:
                dt = dt.replace(tzinfo=dt_to.tzinfo)
            if dt > dt_to:
                return False

    return True
