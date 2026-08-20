"""
Depth alignment and vertical water column filtering for Phase 5 Data Fusion.

Ensures strict unit compatibility (canonical depth in meters, depth >= 0).
Never silently assumes or converts unknown depth units.
"""

from typing import Any, Dict, List, Optional, Union


def is_within_depth_range(
    depth: Optional[float],
    depth_min: Optional[float] = None,
    depth_max: Optional[float] = None
) -> bool:
    """
    Checks if a depth value (in meters) falls within [depth_min, depth_max].
    If depth is None, returns False (unknown depth cannot satisfy an explicit depth filter).
    """
    if depth is None:
        return False

    try:
        d = float(depth)
    except (ValueError, TypeError):
        return False

    if depth_min is not None and d < float(depth_min):
        return False
    if depth_max is not None and d > float(depth_max):
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
        tolerance_meters: Maximum allowed vertical distance in meters
        allow_missing: If True, allows matching when depth is None on either/both observations
                      (useful for unstratified surface catches). Defaults to False for strict 3D matching.

    Returns:
        bool indicating depth compatibility.
    """
    if depth1 is None or depth2 is None:
        return allow_missing

    try:
        d1 = float(depth1)
        d2 = float(depth2)
    except (ValueError, TypeError):
        return False

    if tolerance_meters < 0:
        return False

    return abs(d1 - d2) <= tolerance_meters
