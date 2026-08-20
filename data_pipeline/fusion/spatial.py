"""
Spatial alignment and geographic distance calculations for Phase 5 Data Fusion.

Implements rigorous spherical geodesic distance (Haversine formula) and bounding-box
filtering. Never uses simplistic degree-to-km multiplication that fails across latitudes.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

# WGS84 Mean Earth Radius in kilometers (IUGG standard)
EARTH_RADIUS_KM = 6371.0088


def is_valid_coordinate(lat: Any, lon: Any) -> bool:
    """
    Validates that latitude and longitude are finite numbers within physical bounds:
    - Latitude: [-90.0, 90.0]
    - Longitude: [-180.0, 180.0]
    """
    if lat is None or lon is None:
        return False
    try:
        f_lat = float(lat)
        f_lon = float(lon)
    except (ValueError, TypeError):
        return False

    if not (math.isfinite(f_lat) and math.isfinite(f_lon)):
        return False

    return (-90.0 <= f_lat <= 90.0) and (-180.0 <= f_lon <= 180.0)


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
    if not is_valid_coordinate(lat1, lon1) or not is_valid_coordinate(lat2, lon2):
        raise ValueError(
            "Invalid coordinates: latitudes must be in [-90, 90] and longitudes in [-180, 180], and values must be finite"
        )

    f_lat1, f_lon1 = float(lat1), float(lon1)
    f_lat2, f_lon2 = float(lat2), float(lon2)

    # Fast path for identical points
    if f_lat1 == f_lat2 and f_lon1 == f_lon2:
        return 0.0

    phi1 = math.radians(f_lat1)
    phi2 = math.radians(f_lat2)
    delta_phi = math.radians(f_lat2 - f_lat1)
    delta_lambda = math.radians(f_lon2 - f_lon1)

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
    Returns False if any coordinate is missing/invalid or radius is negative/non-finite.
    """
    if not is_valid_coordinate(lat1, lon1) or not is_valid_coordinate(lat2, lon2):
        return False

    try:
        radius = float(max_radius_km)
        if not math.isfinite(radius) or radius < 0.0:
            return False
    except (ValueError, TypeError):
        return False

    return haversine_distance_km(float(lat1), float(lon1), float(lat2), float(lon2)) <= radius


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
    if not is_valid_coordinate(lat, lon):
        return False
    if not bbox or len(bbox) != 4:
        raise ValueError("bbox must contain exactly 4 coordinates: [west, south, east, north]")

    west, south, east, north = bbox[0], bbox[1], bbox[2], bbox[3]

    if not (is_valid_coordinate(south, west) and is_valid_coordinate(north, east)):
        return False

    f_lat, f_lon = float(lat), float(lon)
    f_west, f_south, f_east, f_north = float(west), float(south), float(east), float(north)

    # Standard bounds check
    lat_ok = f_south <= f_lat <= f_north
    
    # Longitude check (handles standard as well as antimeridian crossing if east < west)
    if f_west <= f_east:
        lon_ok = f_west <= f_lon <= f_east
    else:
        # Crosses the antimeridian (-180 / +180)
        lon_ok = f_lon >= f_west or f_lon <= f_east

    return lat_ok and lon_ok


def compute_bounding_box(
    coordinates: List[Tuple[float, float]]
) -> Optional[Dict[str, float]]:
    """
    Calculates the spatial extent (envelope) for a collection of (lat, lon) coordinates.
    Returns None if no valid coordinates are provided.
    """
    valid_coords = [
        (float(c[0]), float(c[1]))
        for c in coordinates
        if len(c) >= 2 and is_valid_coordinate(c[0], c[1])
    ]
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
