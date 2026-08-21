"""
Schema mapping and column normalization for Phase 4.
Maps diverse raw input field names to canonical platform field names.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from data_pipeline.quality_standardisation.models import (
    IssueSeverity,
    TransformationRecord,
    ValidationIssue,
)


# Canonical platform field definitions and known aliases
DEFAULT_COLUMN_ALIASES: Dict[str, List[str]] = {
    # Core spatial / temporal / provenance fields
    "latitude": [
        "lat", "latitude", "lat_dd", "lat_deg", "decimal_latitude", "dec_lat",
        "y", "station_lat", "sample_lat", "latitude_degrees"
    ],
    "longitude": [
        "lon", "long", "longitude", "lon_dd", "lon_deg", "decimal_longitude", "dec_lon",
        "x", "station_lon", "sample_lon", "longitude_degrees"
    ],
    "time": [
        "time", "timestamp", "datetime", "date_time", "date", "sampling_date",
        "observation_time", "time_utc", "utc_time", "sample_time", "event_date"
    ],
    "depth": [
        "depth", "depth_m", "depth_meters", "z", "water_depth", "sample_depth",
        "sounding", "bottom_depth", "pressure_depth"
    ],
    "station": [
        "station", "station_id", "station_name", "station_no", "station_number",
        "site", "site_id", "sampling_station", "stn_no", "stn"
    ],
    "sample": [
        "sample", "sample_id", "sample_code", "sample_no", "specimen_id", "event_id"
    ],
    "species": [
        "species", "scientific_name", "taxon", "taxa", "species_name", "organism_name"
    ],
    "dataset": [
        "dataset", "dataset_id", "dataset_name", "cruise", "cruise_id", "survey_id"
    ],
    "source": [
        "source", "data_source", "institution", "provider", "vessel", "vessel_name"
    ],

    # Oceanographic measurements
    "temperature": [
        "temperature", "temp", "temp_c", "temp_deg_c", "water_temp", "sst",
        "sea_water_temperature", "ctd_temp", "t_degc", "t"
    ],
    "salinity": [
        "salinity", "sal", "sal_psu", "practical_salinity", "sea_water_salinity",
        "ctd_sal", "s_psu", "s"
    ],
    "dissolved_oxygen": [
        "dissolved_oxygen", "do", "d_o", "oxygen", "o2", "do_mg_l", "do_mgl",
        "oxygen_concentration", "ctd_oxygen", "o2_conc"
    ],
    "chlorophyll": [
        "chlorophyll", "chlorophyll_a", "chl", "chla", "chl_a", "fluorescence",
        "chl_mg_m3", "chlorophyll_concentration"
    ],
    "ph": [
        "ph", "sea_water_ph", "ph_total", "water_ph"
    ],
    "pressure": [
        "pressure", "press", "dbar", "pressure_dbar", "sea_water_pressure"
    ],
    "turbidity": [
        "turbidity", "turb", "ntu", "turbidity_ntu"
    ],
    "conductivity": [
        "conductivity", "cond", "c_ms_cm", "electrical_conductivity"
    ],

    # Fisheries measurements
    "catch_weight_kg": [
        "catch_weight", "catch_weight_kg", "catch_kg", "weight_kg", "total_catch",
        "landings_kg", "catch_amount", "catch_qty"
    ],
    "effort_hours": [
        "effort_hours", "fishing_effort", "effort_hr", "hours_fished", "duration_hours",
        "trawl_duration", "effort"
    ],
    "gear_type": [
        "gear_type", "gear", "fishing_gear", "gear_code", "method"
    ],
    "fishing_zone": [
        "fishing_zone", "zone", "fao_area", "eez_zone", "grid", "area_code"
    ],
    "vessel_name": [
        "vessel_name", "vessel", "boat_name", "ship_name", "craft"
    ],
    "species_common_name": [
        "species_common_name", "common_name", "local_name", "vernacular_name"
    ],
    "species_scientific_name": [
        "species_scientific_name", "scientific_name", "species_latin_name"
    ],

    # Biodiversity / Darwin Core fields
    "individual_count": [
        "individual_count", "count", "abundance", "specimen_count", "quantity"
    ],
    "taxon_rank": [
        "taxon_rank", "rank", "taxonomic_rank"
    ],
    "basis_of_record": [
        "basis_of_record", "record_basis", "observation_type"
    ]
}


def _normalize_key(key: str) -> str:
    """Cleans a column name for fuzzy matching (lowercase, alphanumeric + single underscore)."""
    k = str(key).strip().lower()
    k = re.sub(r"[\s\-\.\/\(\)\[\]]+", "_", k)
    k = re.sub(r"_+", "_", k).strip("_")
    return k


class SchemaMapper:
    """Maps raw record column headers to standard canonical platform fields."""

    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        self.alias_to_canonical: Dict[str, str] = {}
        self._build_alias_lookup()
        
        # Apply any custom overrides supplied by the user/caller
        if custom_mapping:
            for raw_col, target_col in custom_mapping.items():
                self.alias_to_canonical[_normalize_key(raw_col)] = target_col.strip()

    def _build_alias_lookup(self) -> None:
        for canonical, aliases in DEFAULT_COLUMN_ALIASES.items():
            # Canonical itself maps to canonical
            self.alias_to_canonical[_normalize_key(canonical)] = canonical
            for alias in aliases:
                self.alias_to_canonical[_normalize_key(alias)] = canonical

    def map_columns(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ValidationIssue], List[TransformationRecord], List[str]]:
        """
        Maps column names across all input records.
        Returns:
            - mapped_records: List of records with canonical keys where matches were found.
            - issues: Validation issues describing unmapped columns or conflicts.
            - transformations: Provenance transformations recording renamed fields.
            - unmapped_columns: List of columns that could not be mapped to standard fields.
        """
        if not records:
            return [], [], [], []

        # Inspect all unique columns present in the input dataset
        sample_keys: Set[str] = set()
        for r in records:
            sample_keys.update(r.keys())

        column_mapping: Dict[str, str] = {}
        unmapped_columns: List[str] = []
        issues: List[ValidationIssue] = []
        transformations: List[TransformationRecord] = []

        # Determine mapping for each column
        for raw_col in sample_keys:
            norm = _normalize_key(raw_col)
            if norm in self.alias_to_canonical:
                canonical = self.alias_to_canonical[norm]
                column_mapping[raw_col] = canonical
            else:
                column_mapping[raw_col] = raw_col  # Keep original name intact
                unmapped_columns.append(raw_col)

        if unmapped_columns:
            issues.append(
                ValidationIssue(
                    check="schema_mapping",
                    column="dataset",
                    severity=IssueSeverity.INFO,
                    message=f"Columns retained as non-standard domain attributes: {', '.join(unmapped_columns)}",
                    details={"unmapped_columns": unmapped_columns}
                )
            )

        # Apply mapping to all records
        mapped_records: List[Dict[str, Any]] = []
        for idx, row in enumerate(records):
            new_row: Dict[str, Any] = {}
            for k, v in row.items():
                target_k = column_mapping.get(k, k)
                new_row[target_k] = v
                if target_k != k:
                    transformations.append(
                        TransformationRecord(
                            column=target_k,
                            row_index=idx,
                            original_value=k,
                            transformed_value=target_k,
                            rule=f"Column alias mapping: '{k}' -> '{target_k}'"
                        )
                    )
            mapped_records.append(new_row)

        return mapped_records, issues, transformations, unmapped_columns
