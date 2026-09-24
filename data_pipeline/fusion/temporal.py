"""
Temporal alignment and timestamp comparison for Phase 5 Data Fusion.

Preserves Phase 4 timezone semantics:
- Normalizes timezone-aware timestamps to standard UTC for precise delta calculations.
- Preserves naive/local timestamps without assuming UTC/IST or silently inventing offsets.
- Rejects mixed aware/naive comparisons without fabricating or stripping timezone information.
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
        float hours difference, or None if either timestamp is missing or mixed aware/naive.
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
        # Mixed aware and naive: cannot determine exact physical delta without inventing timezone
        return None


def is_within_temporal_window(
    time1: Optional[Union[str, datetime]],
    time2: Optional[Union[str, datetime]],
    window_hours: float
) -> bool:
    """
    Checks if two timestamps are within a given window (in hours).
    Returns False if either timestamp is None, missing, or incompatible.
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
    Rejects comparisons between mixed aware/naive timestamps.
    """
    if ts is None:
        return False

    dt = parse_marine_timestamp(ts)
    if dt is None:
        return False

    if date_from is not None:
        dt_from = parse_marine_timestamp(date_from)
        if dt_from is None:
            return False
        # Reconcile tz awareness
        if dt.tzinfo is not None and dt_from.tzinfo is not None:
            if dt.astimezone(timezone.utc) < dt_from.astimezone(timezone.utc):
                return False
        elif dt.tzinfo is None and dt_from.tzinfo is None:
            if dt < dt_from:
                return False
        else:
            # Mixed awareness: cannot compare safely
            return False

    if date_to is not None:
        dt_to = parse_marine_timestamp(date_to)
        if dt_to is None:
            return False
        # Reconcile tz awareness
        if dt.tzinfo is not None and dt_to.tzinfo is not None:
            if dt.astimezone(timezone.utc) > dt_to.astimezone(timezone.utc):
                return False
        elif dt.tzinfo is None and dt_to.tzinfo is None:
            if dt > dt_to:
                return False
        else:
            # Mixed awareness: cannot compare safely
            return False

    return True
