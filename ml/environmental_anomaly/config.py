"""
Configuration settings for Environmental Anomaly Detection ML Pipeline.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ML_MODULE_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data" / "environmental_anomaly"
MODELS_DIR = ROOT_DIR / "models" / "environmental_anomaly"
RESULTS_DIR = ROOT_DIR / "results" / "environmental_anomaly"

# Canonical variable name aliases for robust NetCDF/HDF5/CSV reading
VARIABLE_ALIASES: Dict[str, List[str]] = {
    "sst": [
        "analysed_sst",
        "sst",
        "thetao",
        "sea_surface_temperature",
        "surface_temperature",
        "temperature",
    ],
    "lat": ["lat", "latitude", "nav_lat"],
    "lon": ["lon", "longitude", "nav_lon"],
    "time": ["time", "timestamp", "date", "time_counter"],
    "analysis_error": ["analysis_error", "sst_error", "error", "uncertainty"],
    "sea_ice_fraction": ["sea_ice_fraction", "ice_fraction", "siconc", "ice"],
    "mask": ["mask", "land_mask", "lsmask", "flags"],
}

# Physical bounds for marine oceanographic validation
SST_MIN_CELSIUS: float = -3.0
SST_MAX_CELSIUS: float = 45.0
KELVIN_CELSIUS_OFFSET: float = 273.15
KELVIN_DETECTION_THRESHOLD: float = 200.0  # If values > 200, assume Kelvin

# Study Region: Strict IHO S-23 Arabian Sea Demarcation
STUDY_REGION_NAME: str = "Arabian Sea (Strict IHO S-23)"
DATASET_LAT_MIN: float = 5.0
DATASET_LAT_MAX: float = 25.0
DATASET_LON_MIN: float = 50.0
DATASET_LON_MAX: float = 78.0

# Geographic boundary demarcation points (IHO S-23, Section 38)
# 1. Persian Gulf: west of Strait of Hormuz (lon <= 56.5°E, lat >= 23.5°N)
PERSIAN_GULF_LON_MAX: float = 56.5
PERSIAN_GULF_LAT_MIN: float = 23.5

# 2. Gulf of Oman limit line: Ras al Hadd, Oman (59.80°E, 22.53°N) to Cape Jiwani, Pakistan (61.74°E, 25.02°N)
RAS_AL_HADD_LON: float = 59.80
RAS_AL_HADD_LAT: float = 22.53
CAPE_JIWANI_LON: float = 61.74
CAPE_JIWANI_LAT: float = 25.02
GULF_OF_OMAN_LINE_SLOPE: float = 1.28350515  # (25.02 - 22.53) / (61.74 - 59.80)

# 3. Gulf of Aden limit line: Ras Asir, Somalia (51.28°E, 11.83°N) to Ras Fartak, Yemen (52.23°E, 15.63°N)
RAS_ASIR_LON: float = 51.28
RAS_ASIR_LAT: float = 11.83
RAS_FARTAK_LON: float = 52.23
RAS_FARTAK_LAT: float = 15.63
GULF_OF_ADEN_LINE_SLOPE: float = 4.0  # (15.63 - 11.83) / (52.23 - 51.28)


@dataclass
class AnomalyModelConfig:
    """Configuration for Isolation Forest Anomaly Detection Model."""
    n_estimators: int = 150
    contamination: Union[float, str] = 0.03
    max_samples: Union[int, float, str] = "auto"
    random_state: int = 42
    n_jobs: int = -1

    # Severity scoring thresholds (0-100 normalized score)
    score_threshold_moderate: float = 60.0
    score_threshold_high: float = 75.0
    score_threshold_critical: float = 85.0


@dataclass
class BaselineConfig:
    """Configuration for SST Climatological/Seasonal Baseline calculation."""
    method: str = "spatial_monthly"  # 'spatial_monthly' or 'harmonic'
    grid_resolution_deg: float = 1.0  # Spatial cell binning (degrees)
    min_observations_per_cell: int = 2
    regional_fallback_lat_bins_deg: float = 5.0  # Fallback latitudinal band width


@dataclass
class PipelineConfig:
    """Master pipeline configuration."""
    model: AnomalyModelConfig = field(default_factory=AnomalyModelConfig)
    baseline: BaselineConfig = field(default_factory=BaselineConfig)
    
    # Study Region & Domain Filtering
    apply_arabian_sea_mask: bool = True
    
    # Feature selection
    use_analysis_error: bool = True
    use_sea_ice_fraction: bool = True  # Only included if variance > 0
    use_cyclic_time: bool = True
    
    # Paths
    raw_data_dir: Path = DATA_DIR
    models_dir: Path = MODELS_DIR
    results_dir: Path = RESULTS_DIR


default_config = PipelineConfig()

