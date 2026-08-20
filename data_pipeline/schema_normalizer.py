"""
Schema Normalizer for CMLRE Datasets.
Maps non-standard / vendor column headers to canonical CMLRE platform headers
while strictly preserving all source columns.
"""

from typing import Dict, List, Tuple
import pandas as pd

# Canonical marine field aliases
CANONICAL_COLUMN_MAPPINGS: Dict[str, List[str]] = {
    "latitude": [
        "latitude", "decimallatitude", "lat", "lat_deg", "lat_dd", "y", "geo_lat"
    ],
    "longitude": [
        "longitude", "decimallongitude", "lon", "long", "lon_deg", "lon_dd", "x", "geo_lon"
    ],
    "timestamp": [
        "timestamp", "time", "observed_at", "recorded_at", "eventdate", "date_time", "datetime", "date"
    ],
    "depth": [
        "depth", "minimumdepthinmeters", "depth_m", "depth_meters", "prdm", "pressure", "sample_depth"
    ],
    "temperature": [
        "temperature", "temp", "temp_c", "temperature_c", "t090c", "sst", "sea_surface_temperature"
    ],
    "salinity": [
        "salinity", "sal", "sal00", "salinity_psu", "sss", "sea_surface_salinity"
    ],
    "dissolved_oxygen": [
        "dissolved_oxygen", "oxygen", "do", "do_mg_l", "sbeox0ml/l", "oxygen_ml_l"
    ],
    "chlorophyll": [
        "chlorophyll", "chlorophyll_a", "chl_a", "chla", "flecofl", "fleco-afl", "fluorescence"
    ],
    "scientific_name": [
        "scientificname", "species_name", "species", "taxa", "taxon_name", "taxonomy"
    ],
    "catch_weight_kg": [
        "catch_weight_kg", "catch_weight", "catch_kg", "total_catch_kg", "landing_weight"
    ],
    "gear_type": [
        "gear_type", "gear", "trawl_type"
    ],
    "effort_hours": [
        "effort_hours", "effort", "trawl_duration_hrs", "soak_time"
    ],
    "individual_count": [
        "individualcount", "organismquantity", "read_count", "reads", "count"
    ]
}


def build_alias_lookup() -> Dict[str, str]:
    """Builds a reverse lookup mapping cleaned alias -> canonical column name."""
    lookup: Dict[str, str] = {}
    for canonical, aliases in CANONICAL_COLUMN_MAPPINGS.items():
        for alias in aliases:
            lookup[alias.lower().replace("_", "").replace(" ", "").replace("-", "")] = canonical
    return lookup


_LOOKUP = build_alias_lookup()


def normalize_dataframe_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Normalizes DataFrame columns to canonical names.
    Returns:
        normalized_df: Copy of DataFrame with standardized column names
        applied_mappings: Dict mapping original column name -> canonical column name
    """
    applied_mappings: Dict[str, str] = {}
    new_columns: List[str] = []
    used_canonicals = set()

    for col in df.columns:
        cleaned_col = str(col).lower().replace("_", "").replace(" ", "").replace("-", "")
        if cleaned_col in _LOOKUP:
            canonical = _LOOKUP[cleaned_col]
            if canonical not in used_canonicals:
                new_columns.append(canonical)
                applied_mappings[str(col)] = canonical
                used_canonicals.add(canonical)
            else:
                # Keep original to avoid duplicate column collision
                new_columns.append(str(col))
        else:
            # Preserve unknown / custom columns
            new_columns.append(str(col))

    normalized_df = df.copy()
    normalized_df.columns = new_columns
    return normalized_df, applied_mappings
