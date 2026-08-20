"""
Depth alignment and vertical water column filtering for Phase 5 Data Fusion.

Ensures strict unit compatibility (canonical depth in meters, depth >= 0).
Never silently assumes or converts unknown depth units.
"""

import math
from typing import Any, Dict, List, Optional, Union


def is_within_depth_range(
    depth: Optional[float],
    depth_min: Optional[float] = None,
    depth_max: Optional[float] = None
) -> bool:
    """
    Checks if a depth value (in meters) falls within [depth_min, depth_max].
    Rejects non-finite or negative depths, depth_min, and depth_max.
    If depth is None, returns False (unknown depth cannot satisfy an explicit depth filter).
    """
    if depth is None:
        return False

    try:
        d = float(depth)
    except (ValueError, TypeError):
        return False

    if not math.isfinite(d) or d < 0.0:
        return False

    if depth_min is not None:
        try:
            d_min = float(depth_min)
            if not math.isfinite(d_min) or d_min < 0.0:
                return False
            if d < d_min:
                return False
        except (ValueError, TypeError):
            return False

    if depth_max is not None:
        try:
            d_max = float(depth_max)
            if not math.isfinite(d_max) or d_max < 0.0:
                return False
            if d > d_max:
                return False
        except (ValueError, TypeError):
            return False

    return True


def is_within_depth_tolerance(
    depth1: Optional[float],
    depth2: Optional[float],
    tolerance_meters: float,
    allow_missing: bool = False
) -> bool:
    """
    Checks if two depth observations (in meters) are within a specified vertical tolerance.

    Args:
        depth1: Depth in meters of observation 1
        depth2: Depth in meters of observation 2
        tolerance_meters: Maximum allowed vertical distance in meters (must be non-negative and finite)
        allow_missing: If True, allows matching when depth is None on either/both observations
                      (useful for unstratified surface catches). Defaults to False for strict 3D matching.

    Returns:
        bool indicating depth compatibility.
    """
    try:
        tol = float(tolerance_meters)
        if not math.isfinite(tol) or tol < 0.0:
            return False
    except (ValueError, TypeError):
        return False

    if depth1 is None or depth2 is None:
        return allow_missing

    try:
        d1 = float(depth1)
        d2 = float(depth2)
    except (ValueError, TypeError):
        return False

    if not math.isfinite(d1) or d1 < 0.0 or not math.isfinite(d2) or d2 < 0.0:
        return False

    return abs(d1 - d2) <= tol
