"""
Preprocessing and Quality Control for Marine Environmental Observations.

Includes strict International Hydrographic Organization (IHO S-23) geographic
demarcation for the Arabian Sea study domain, excluding the Persian Gulf,
Gulf of Oman, and Gulf of Aden.
"""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .config import (
    CAPE_JIWANI_LAT,
    CAPE_JIWANI_LON,
    GULF_OF_ADEN_LINE_SLOPE,
    GULF_OF_OMAN_LINE_SLOPE,
    KELVIN_CELSIUS_OFFSET,
    KELVIN_DETECTION_THRESHOLD,
    PERSIAN_GULF_LAT_MIN,
    PERSIAN_GULF_LON_MAX,
    RAS_AL_HADD_LAT,
    RAS_AL_HADD_LON,
    RAS_ASIR_LAT,
    RAS_ASIR_LON,
    RAS_FARTAK_LAT,
    RAS_FARTAK_LON,
    SST_MAX_CELSIUS,
    SST_MIN_CELSIUS,
    STUDY_REGION_NAME,
)

logger = logging.getLogger(__name__)


def compute_arabian_sea_subbasin_masks(
    latitude: Union[np.ndarray, pd.Series],
    longitude: Union[np.ndarray, pd.Series],
) -> Dict[str, np.ndarray]:
    """
    Vectorized computation of IHO S-23 Arabian Sea and adjacent marginal sub-basin masks.

    Demarcation logic (IHO Publication S-23, Section 38):
    1. Persian Gulf: west of the Strait of Hormuz (lon <= 56.5°E, lat >= 23.5°N)
    2. Gulf of Oman: northwest of the geodesic line connecting Ras al Hadd, Oman
       (59.80°E, 22.53°N) to Cape Jiwani, Pakistan (61.74°E, 25.02°N).
       Line: lat = 22.53 + 1.283505 * (lon - 59.80)
    3. Gulf of Aden: west of the geodesic line connecting Ras Asir, Somalia
       (51.28°E, 11.83°N) to Ras Fartak, Yemen (52.23°E, 15.63°N).
       Line: lat = 11.83 + 4.0 * (lon - 51.28)
    4. Arabian Sea (Strict IHO S-23): waters within dataset bounding box excluding
       Persian Gulf, Gulf of Oman, and Gulf of Aden.

    Returns:
        Dict[str, np.ndarray] containing boolean masks:
        - 'is_persian_gulf'
        - 'is_gulf_of_oman'
        - 'is_gulf_of_aden'
        - 'is_arabian_sea'
    """
    lat = np.asarray(latitude, dtype=np.float64)
    lon = np.asarray(longitude, dtype=np.float64)

    # 1. Persian Gulf: west of Strait of Hormuz (lon <= 56.5°E, lat >= 23.5°N)
    is_pg = (lon <= PERSIAN_GULF_LON_MAX) & (lat >= PERSIAN_GULF_LAT_MIN)

    # 2. Gulf of Oman: Northwest of Ras al Hadd -> Cape Jiwani limit line
    is_go = ~is_pg & (
        ((lon <= RAS_AL_HADD_LON) & (lat >= 22.50))
        | (
            (lon > RAS_AL_HADD_LON)
            & (lon <= CAPE_JIWANI_LON)
            & (lat >= (RAS_AL_HADD_LAT + GULF_OF_OMAN_LINE_SLOPE * (lon - RAS_AL_HADD_LON)))
        )
    )

    # 3. Gulf of Aden: West of Ras Asir -> Ras Fartak limit line
    is_ga = (
        ((lon < RAS_ASIR_LON) & (lat >= 10.0) & (lat <= 16.0))
        | (
            (lon >= RAS_ASIR_LON)
            & (lon <= RAS_FARTAK_LON)
            & (lat >= 10.0)
            & (lat <= (RAS_ASIR_LAT + GULF_OF_ADEN_LINE_SLOPE * (lon - RAS_ASIR_LON)))
        )
    )

    # 4. Strict IHO S-23 Arabian Sea: excludes all 3 marginal basins
    is_as = ~(is_pg | is_go | is_ga)

    return {
        "is_persian_gulf": is_pg,
        "is_gulf_of_oman": is_go,
        "is_gulf_of_aden": is_ga,
        "is_arabian_sea": is_as,
    }


@dataclass
class PreprocessingAuditReport:
    """Audit metrics for preprocessing and geographic masking steps."""
    initial_record_count: int
    final_record_count: int
    dropped_missing_sst: int
    dropped_invalid_coords: int
    dropped_land_pixels: int
    dropped_persian_gulf: int
    dropped_gulf_of_oman: int
    dropped_gulf_of_aden: int
    dropped_out_of_bounds_sst: int
    kelvin_converted: bool
    arabian_sea_mask_applied: bool = True

    @property
    def retention_rate_pct(self) -> float:
        if self.initial_record_count <= 0:
            return 0.0
        return round((self.final_record_count / self.initial_record_count) * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_record_count": self.initial_record_count,
            "final_record_count": self.final_record_count,
            "dropped_missing_sst": self.dropped_missing_sst,
            "dropped_invalid_coords": self.dropped_invalid_coords,
            "dropped_land_pixels": self.dropped_land_pixels,
            "dropped_persian_gulf": self.dropped_persian_gulf,
            "dropped_gulf_of_oman": self.dropped_gulf_of_oman,
            "dropped_gulf_of_aden": self.dropped_gulf_of_aden,
            "dropped_marginal_seas_total": (
                self.dropped_persian_gulf + self.dropped_gulf_of_oman + self.dropped_gulf_of_aden
            ),
            "dropped_out_of_bounds_sst": self.dropped_out_of_bounds_sst,
            "retention_rate_pct": round(
                (self.final_record_count / self.initial_record_count * 100)
                if self.initial_record_count > 0 else 0.0, 2
            ),
            "kelvin_converted": self.kelvin_converted,
            "arabian_sea_mask_applied": self.arabian_sea_mask_applied,
            "study_region": STUDY_REGION_NAME if self.arabian_sea_mask_applied else "Full Rectangular Bounding Box",
        }


class EnvironmentalPreprocessor:
    """
    Cleans, normalizes, and filters marine environmental observations with strict
    IHO S-23 Arabian Sea geographic domain masking.
    """

    def __init__(
        self,
        sst_min_c: float = SST_MIN_CELSIUS,
        sst_max_c: float = SST_MAX_CELSIUS,
        filter_land_mask: bool = True,
        apply_arabian_sea_mask: bool = True,
        normalize_longitude: bool = True,
    ):
        self.sst_min_c = sst_min_c
        self.sst_max_c = sst_max_c
        self.filter_land_mask = filter_land_mask
        self.apply_arabian_sea_mask = apply_arabian_sea_mask
        self.normalize_longitude = normalize_longitude
        self.last_audit: Optional[PreprocessingAuditReport] = None

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, PreprocessingAuditReport]:
        """Applies full preprocessing pipeline and records audit trail."""
        return self.transform(df)

    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, PreprocessingAuditReport]:
        """
        Cleans and standardizes input environmental DataFrame.
        """
        initial_count = len(df)
        if initial_count == 0:
            empty_audit = PreprocessingAuditReport(
                initial_record_count=0,
                final_record_count=0,
                dropped_missing_sst=0,
                dropped_invalid_coords=0,
                dropped_land_pixels=0,
                dropped_persian_gulf=0,
                dropped_gulf_of_oman=0,
                dropped_gulf_of_aden=0,
                dropped_out_of_bounds_sst=0,
                kelvin_converted=False,
                arabian_sea_mask_applied=self.apply_arabian_sea_mask,
            )
            self.last_audit = empty_audit
            return df.copy(), empty_audit

        cleaned = df.copy()

        # 1. Coordinate Validation (Lat: [-90, 90], Lon: [-180, 360])
        valid_coords = (
            cleaned["latitude"].notna()
            & cleaned["longitude"].notna()
            & (cleaned["latitude"] >= -90.0)
            & (cleaned["latitude"] <= 90.0)
        )
        dropped_coords = int((~valid_coords).sum())
        cleaned = cleaned[valid_coords].copy()

        # Normalize longitude to [-180.0, 180.0]
        if self.normalize_longitude:
            cleaned["longitude"] = cleaned["longitude"].apply(
                lambda lon: ((lon + 180.0) % 360.0) - 180.0
            )

        # 2. SST Missing / Fill Value handling
        valid_sst = (
            cleaned["analysed_sst"].notna()
            & (cleaned["analysed_sst"] > -900)
            & (cleaned["analysed_sst"] != -32768)
            & (cleaned["analysed_sst"] != -32767)
            & (cleaned["analysed_sst"] != 32767)
        )
        dropped_missing_sst = int((~valid_sst).sum())
        cleaned = cleaned[valid_sst].copy()

        # 3. Land Mask Filtering (if mask column present)
        dropped_land = 0
        if self.filter_land_mask and "mask" in cleaned.columns:
            mask_vals = cleaned["mask"].dropna().unique()
            if 1 in mask_vals:
                is_sea = (cleaned["mask"] == 1)
                dropped_land = int((~is_sea).sum())
                cleaned = cleaned[is_sea].copy()

        # 4. Strict IHO S-23 Arabian Sea Geographic Masking
        dropped_pg = 0
        dropped_go = 0
        dropped_ga = 0
        if self.apply_arabian_sea_mask:
            sub_masks = compute_arabian_sea_subbasin_masks(cleaned["latitude"], cleaned["longitude"])
            dropped_pg = int(np.sum(sub_masks["is_persian_gulf"]))
            dropped_go = int(np.sum(sub_masks["is_gulf_of_oman"]))
            dropped_ga = int(np.sum(sub_masks["is_gulf_of_aden"]))
            cleaned = cleaned[sub_masks["is_arabian_sea"]].copy()

        # 5. Automatic Kelvin to Celsius detection (values > 200 K)
        kelvin_converted = False
        is_kelvin = cleaned["analysed_sst"] > KELVIN_DETECTION_THRESHOLD
        if is_kelvin.any():
            cleaned.loc[is_kelvin, "analysed_sst"] = cleaned.loc[is_kelvin, "analysed_sst"] - KELVIN_CELSIUS_OFFSET
            kelvin_converted = True

        # 6. Physical Oceanographic Range Checks
        in_bounds = (
            (cleaned["analysed_sst"] >= self.sst_min_c)
            & (cleaned["analysed_sst"] <= self.sst_max_c)
        )
        dropped_bounds = int((~in_bounds).sum())
        cleaned = cleaned[in_bounds].copy()

        final_count = len(cleaned)
        audit = PreprocessingAuditReport(
            initial_record_count=initial_count,
            final_record_count=final_count,
            dropped_missing_sst=dropped_missing_sst,
            dropped_invalid_coords=dropped_coords,
            dropped_land_pixels=dropped_land,
            dropped_persian_gulf=dropped_pg,
            dropped_gulf_of_oman=dropped_go,
            dropped_gulf_of_aden=dropped_ga,
            dropped_out_of_bounds_sst=dropped_bounds,
            kelvin_converted=kelvin_converted,
            arabian_sea_mask_applied=self.apply_arabian_sea_mask,
        )
        self.last_audit = audit
        logger.info(
            f"Preprocessing completed: {initial_count:,} -> {final_count:,} records retained "
            f"({audit.to_dict()['retention_rate_pct']}%). "
            f"Excluded: PG={dropped_pg:,}, GO={dropped_go:,}, GA={dropped_ga:,}."
        )
        return cleaned.reset_index(drop=True), audit
