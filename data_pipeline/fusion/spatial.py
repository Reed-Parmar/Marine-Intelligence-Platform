"""
Spatial alignment and geographic distance calculations for Phase 5 Data Fusion.

Implements rigorous spherical geodesic distance (Haversine formula) and bounding-box
filtering. Never uses simplistic degree-to-km multiplication that fails across latitudes.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

# WGS84 Mean Earth Radius in kilometers (IUGG standard)
EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Computes the great-circle distance between two points on the Earth's surface
    using the mathematically rigorous Haversine formula.

    Args:
        lat1: Latitude of point 1 in decimal degrees [-90.0, 90.0]
        lon1: Longitude of point 1 in decimal degrees [-180.0, 180.0]
        lat2: Latitude of point 2 in decimal degrees [-90.0, 90.0]
        lon2: Longitude of point 2 in decimal degrees [-180.0, 180.0]

    Returns:
        Geodesic distance in kilometers.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        raise ValueError("Coordinates cannot be None for distance calculation")

    # Fast path for identical points
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clip a to [0.0, 1.0] to prevent math domain error in asin/atan2 due to floating point inaccuracies
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_KM * c


def is_within_spatial_proximity(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float],
    max_radius_km: float
) -> bool:
    """
    Determines whether two coordinates are within a specified distance threshold.
    Returns False if any coordinate is missing/None.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return False
    if max_radius_km < 0:
        return False

    return haversine_distance_km(lat1, lon1, lat2, lon2) <= max_radius_km


def is_within_bbox(
    lat: Optional[float],
    lon: Optional[float],
    bbox: Union[List[float], Tuple[float, float, float, float]]
) -> bool:
    """
    Checks if a coordinate point falls inside a bounding box.
    
    Standard Bounding Box Format:
        bbox = [west_lon, south_lat, east_lon, north_lat] or [min_lon, min_lat, max_lon, max_lat]
    """
    if lat is None or lon is None:
        return False
    if len(bbox) != 4:
        raise ValueError("bbox must contain exactly 4 coordinates: [west, south, east, north]")

    west, south, east, north = bbox[0], bbox[1], bbox[2], bbox[3]

    # Standard bounds check
    lat_ok = south <= lat <= north
    
    # Longitude check (handles standard as well as antimeridian crossing if east < west)
    if west <= east:
        lon_ok = west <= lon <= east
    else:
        # Crosses the antimeridian (-180 / +180)
        lon_ok = lon >= west or lon <= east

    return lat_ok and lon_ok


def compute_bounding_box(
    coordinates: List[Tuple[float, float]]
) -> Optional[Dict[str, float]]:
    """
    Calculates the spatial extent (envelope) for a collection of (lat, lon) coordinates.
    Returns None if no valid coordinates are provided.
    """
    valid_coords = [c for c in coordinates if c[0] is not None and c[1] is not None]
    if not valid_coords:
        return None

    lats = [c[0] for c in valid_coords]
    lons = [c[1] for c in valid_coords]

    return {
        "lat_min": min(lats),
        "lat_max": max(lats),
        "lon_min": min(lons),
        "lon_max": max(lons),
    }
