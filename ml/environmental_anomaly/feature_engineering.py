"""
Feature Engineering & SST Climatological/Seasonal Baseline for Marine Anomaly Detection.
"""

from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .config import BaselineConfig

logger = logging.getLogger(__name__)


class SSTBaselineCalculator:
    """
    Calculates spatial-temporal seasonal SST baselines from available observations.

    SCIENTIFIC NOTE & LIMITATION:
    When multi-decadal (30-year) climatology is unavailable, this calculator computes
    an empirical spatial-monthly mean baseline from the observed window (e.g., 2-year period).
    Grid cells with sparse coverage fall back gracefully to regional latitudinal bands,
    preserving local seasonality while avoiding overfitting to noise.
    """

    def __init__(self, config: Optional[BaselineConfig] = None):
        self.config = config or BaselineConfig()
        self.grid_res = self.config.grid_resolution_deg
        self.min_obs = self.config.min_observations_per_cell
        self.lat_band_width = self.config.regional_fallback_lat_bins_deg

        # Lookup structures
        self.cell_monthly_baseline: Dict[str, float] = {}
        self.lat_band_monthly_baseline: Dict[str, float] = {}
        self.global_monthly_baseline: Dict[int, float] = {}
        self.overall_mean: float = 28.0
        self.is_fitted: bool = False

    def _get_cell_key(self, lat: float, lon: float, month: int) -> str:
        lat_bin = round(math.floor(lat / self.grid_res) * self.grid_res, 2)
        lon_bin = round(math.floor(lon / self.grid_res) * self.grid_res, 2)
        return f"{lat_bin}_{lon_bin}_{month}"

    def _get_lat_band_key(self, lat: float, month: int) -> str:
        band = round(math.floor(lat / self.lat_band_width) * self.lat_band_width, 2)
        return f"{band}_{month}"

    def fit(self, df: pd.DataFrame) -> "SSTBaselineCalculator":
        """Computes empirical baseline lookup tables from training DataFrame."""
        if len(df) == 0:
            raise ValueError("Cannot fit SSTBaselineCalculator on empty DataFrame.")

        logger.info(f"Fitting SST Baseline Calculator on {len(df):,} observations...")
        self.overall_mean = round(float(df["analysed_sst"].mean()), 3)

        # 1. Global Monthly Baseline
        global_grp = df.groupby("month")["analysed_sst"].mean()
        self.global_monthly_baseline = {int(m): round(float(v), 3) for m, v in global_grp.items()}

        # 2. Regional Latitudinal Band Monthly Baseline
        temp_df = df.copy()
        temp_df["lat_band"] = temp_df["latitude"].apply(
            lambda l: round(math.floor(l / self.lat_band_width) * self.lat_band_width, 2)
        )
        band_grp = temp_df.groupby(["lat_band", "month"])["analysed_sst"].mean()
        self.lat_band_monthly_baseline = {
            f"{band}_{month}": round(float(v), 3)
            for (band, month), v in band_grp.items()
        }

        # 3. High-Resolution Spatial Grid Cell Monthly Baseline
        temp_df["cell_lat"] = temp_df["latitude"].apply(
            lambda l: round(math.floor(l / self.grid_res) * self.grid_res, 2)
        )
        temp_df["cell_lon"] = temp_df["longitude"].apply(
            lambda l: round(math.floor(l / self.grid_res) * self.grid_res, 2)
        )
        cell_grp = temp_df.groupby(["cell_lat", "cell_lon", "month"])["analysed_sst"].agg(["count", "mean"])
        
        # Only retain cells meeting minimum observation count
        for (clat, clon, month), row in cell_grp.iterrows():
            if row["count"] >= self.min_obs:
                key = f"{clat}_{clon}_{month}"
                self.cell_monthly_baseline[key] = round(float(row["mean"]), 3)

        self.is_fitted = True
        logger.info(
            f"Baseline Calculator fitted: {len(self.cell_monthly_baseline):,} spatial grid cells, "
            f"{len(self.lat_band_monthly_baseline):,} latitudinal bands."
        )
        return self

    def get_baseline(self, lat: float, lon: float, month: int) -> float:
        """Retrieves expected baseline SST with hierarchical fallback."""
        if not self.is_fitted:
            return self.overall_mean

        # Level 1: Precise spatial cell baseline
        cell_key = self._get_cell_key(lat, lon, month)
        if cell_key in self.cell_monthly_baseline:
            return self.cell_monthly_baseline[cell_key]

        # Level 2: Latitudinal band seasonal baseline
        band_key = self._get_lat_band_key(lat, month)
        if band_key in self.lat_band_monthly_baseline:
            return self.lat_band_monthly_baseline[band_key]

        # Level 3: Global monthly baseline
        if month in self.global_monthly_baseline:
            return self.global_monthly_baseline[month]

        # Level 4: Overall mean
        return self.overall_mean

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds expected baseline SST and computes sst_anomaly."""
        if not self.is_fitted:
            raise RuntimeError("SSTBaselineCalculator must be fitted before transform.")

        result = df.copy()
        baselines = []
        for _, row in result.iterrows():
            b = self.get_baseline(
                float(row["latitude"]),
                float(row["longitude"]),
                int(row.get("month", 1)),
            )
            baselines.append(b)

        result["baseline_sst"] = baselines
        result["sst_anomaly"] = (result["analysed_sst"] - result["baseline_sst"]).round(3)
        result["sst_abs_anomaly"] = result["sst_anomaly"].abs().round(3)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": asdict(self.config),
            "overall_mean": self.overall_mean,
            "global_monthly_baseline": self.global_monthly_baseline,
            "lat_band_monthly_baseline": self.lat_band_monthly_baseline,
            "cell_monthly_baseline": self.cell_monthly_baseline,
            "is_fitted": self.is_fitted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SSTBaselineCalculator":
        cfg_dict = data.get("config", {})
        config = BaselineConfig(**cfg_dict)
        calc = cls(config)
        calc.overall_mean = data.get("overall_mean", 28.0)
        calc.global_monthly_baseline = {int(k): v for k, v in data.get("global_monthly_baseline", {}).items()}
        calc.lat_band_monthly_baseline = data.get("lat_band_monthly_baseline", {})
        calc.cell_monthly_baseline = data.get("cell_monthly_baseline", {})
        calc.is_fitted = data.get("is_fitted", True)
        return calc


class EnvironmentalFeatureEngineer:
    """
    Extracts features for Isolation Forest Anomaly Detection.
    """

    def __init__(
        self,
        use_analysis_error: bool = True,
        use_sea_ice_fraction: bool = True,
        use_cyclic_time: bool = True,
    ):
        self.use_analysis_error = use_analysis_error
        self.use_sea_ice_fraction = use_sea_ice_fraction
        self.use_cyclic_time = use_cyclic_time

        self.selected_features: List[str] = []
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame) -> "EnvironmentalFeatureEngineer":
        """Identifies active valid features based on data inspection."""
        features = ["sst_anomaly", "analysed_sst", "latitude", "longitude"]

        if self.use_cyclic_time:
            features.extend(["month_sin", "month_cos", "day_sin", "day_cos"])

        # Check analysis_error validity (non-constant and present)
        if self.use_analysis_error and "analysis_error" in df.columns:
            err_valid = df["analysis_error"].dropna()
            if len(err_valid) > 0 and err_valid.std() > 1e-4:
                features.append("analysis_error")
                logger.info("Retained analysis_error as active feature.")
            else:
                logger.info("analysis_error is constant or missing; excluded from active features.")

        # Check sea_ice_fraction validity (must have meaningful non-zero variance)
        if self.use_sea_ice_fraction and "sea_ice_fraction" in df.columns:
            ice_valid = df["sea_ice_fraction"].dropna()
            if len(ice_valid) > 0 and ice_valid.max() > 0.01 and ice_valid.std() > 1e-4:
                features.append("sea_ice_fraction")
                logger.info("Retained sea_ice_fraction as active feature.")
            else:
                logger.info("sea_ice_fraction has negligible variance; excluded.")

        self.selected_features = features
        self.is_fitted = True
        logger.info(f"Feature engineering configured with {len(self.selected_features)} features: {self.selected_features}")
        return self

    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extracts engineered features and returns (enriched_df, feature_matrix_X).
        """
        enriched = df.copy()

        # Cyclic time features
        months = enriched["month"].astype(float) if "month" in enriched.columns else pd.Series(1.0, index=enriched.index)
        enriched["month_sin"] = np.sin(2 * np.pi * months / 12.0).round(4)
        enriched["month_cos"] = np.cos(2 * np.pi * months / 12.0).round(4)

        doy = enriched["day_of_year"].astype(float) if "day_of_year" in enriched.columns else pd.Series(1.0, index=enriched.index)
        enriched["day_sin"] = np.sin(2 * np.pi * doy / 365.25).round(4)
        enriched["day_cos"] = np.cos(2 * np.pi * doy / 365.25).round(4)

        if not self.is_fitted:
            self.fit(enriched)

        # Build feature matrix X (fill missing auxiliary values with median/0)
        X = pd.DataFrame(index=enriched.index)
        for col in self.selected_features:
            if col in enriched.columns:
                val = enriched[col]
                if val.isna().any():
                    val = val.fillna(val.median() if val.notna().any() else 0.0)
                X[col] = val
            else:
                X[col] = 0.0

        return enriched, X

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_features": self.selected_features,
            "use_analysis_error": self.use_analysis_error,
            "use_sea_ice_fraction": self.use_sea_ice_fraction,
            "use_cyclic_time": self.use_cyclic_time,
            "is_fitted": self.is_fitted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentalFeatureEngineer":
        fe = cls(
            use_analysis_error=data.get("use_analysis_error", True),
            use_sea_ice_fraction=data.get("use_sea_ice_fraction", True),
            use_cyclic_time=data.get("use_cyclic_time", True),
        )
        fe.selected_features = data.get("selected_features", [])
        fe.is_fitted = data.get("is_fitted", True)
        return fe
