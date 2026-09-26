"""
Training Pipeline for Marine Environmental Anomaly Detection Model (Isolation Forest).
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .config import AnomalyModelConfig, MODELS_DIR, PipelineConfig
from .feature_engineering import EnvironmentalFeatureEngineer, SSTBaselineCalculator
from .preprocessing import EnvironmentalPreprocessor, PreprocessingAuditReport

logger = logging.getLogger(__name__)


class EnvironmentalAnomalyTrainer:
    """
    Trains and exports the Isolation Forest Environmental Anomaly Detection Model.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.model_cfg = self.config.model
        self.baseline_cfg = self.config.baseline

        self.preprocessor = EnvironmentalPreprocessor(
            apply_arabian_sea_mask=self.config.apply_arabian_sea_mask
        )
        self.baseline_calc = SSTBaselineCalculator(self.baseline_cfg)
        self.feature_engineer = EnvironmentalFeatureEngineer(
            use_analysis_error=self.config.use_analysis_error,
            use_sea_ice_fraction=self.config.use_sea_ice_fraction,
            use_cyclic_time=self.config.use_cyclic_time,
        )

        self.model = IsolationForest(
            n_estimators=self.model_cfg.n_estimators,
            contamination=self.model_cfg.contamination,
            max_samples=self.model_cfg.max_samples,
            random_state=self.model_cfg.random_state,
            n_jobs=self.model_cfg.n_jobs,
        )

        self.is_fitted: bool = False
        self.score_min_raw: float = 0.0
        self.score_max_raw: float = 1.0

    def fit_predict(
        self,
        raw_df: pd.DataFrame,
        dataset_name: str = "environmental_sst_observations",
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes end-to-end pipeline: Preprocessing -> Baseline -> Features -> Fit -> Predict.
        Returns (predicted_df, training_metadata).
        """
        logger.info(f"Starting training pipeline on {len(raw_df):,} raw records...")

        # 1. Preprocessing
        clean_df, audit = self.preprocessor.fit_transform(raw_df)
        if len(clean_df) == 0:
            raise ValueError("All records were filtered out during preprocessing. Check data quality.")

        # 2. SST Climatological/Seasonal Baseline
        clean_df = self.baseline_calc.fit(clean_df).transform(clean_df)

        # 3. Feature Engineering
        enriched_df, X = self.feature_engineer.fit(clean_df).transform(clean_df)

        # 4. Fit Isolation Forest
        logger.info(
            f"Fitting Isolation Forest on {len(X):,} observations with {len(self.feature_engineer.selected_features)} features..."
        )
        self.model.fit(X)
        self.is_fitted = True

        # 5. Predictions & Scoring
        # In sklearn IsolationForest:
        # decision_function: lower means more anomalous (negative for anomalies, positive for inliers)
        # predict: -1 for anomaly, 1 for inlier
        raw_scores = self.model.decision_function(X)
        labels = self.model.predict(X)  # 1 (inlier) or -1 (anomaly)

        self.score_min_raw = float(np.min(raw_scores))
        self.score_max_raw = float(np.max(raw_scores))

        # Normalize score to 0 to 100 where higher = MORE anomalous
        # score_norm = (max_raw - raw_score) / (max_raw - min_raw) * 100
        score_range = max(self.score_max_raw - self.score_min_raw, 1e-6)
        normalized_scores = np.clip(
            ((self.score_max_raw - raw_scores) / score_range) * 100.0, 0.0, 100.0
        ).round(2)

        is_anomaly = labels == -1
        anomaly_count = int(np.sum(is_anomaly))
        anomaly_rate = round(float(anomaly_count / len(enriched_df) * 100), 2)

        enriched_df["anomaly_label"] = labels
        enriched_df["is_anomaly"] = is_anomaly
        enriched_df["anomaly_score"] = normalized_scores
        enriched_df["raw_decision_score"] = raw_scores.round(4)

        # Categorize severity
        severities = []
        for s in normalized_scores:
            if s >= self.model_cfg.score_threshold_critical:
                severities.append("critical")
            elif s >= self.model_cfg.score_threshold_high:
                severities.append("high")
            elif s >= self.model_cfg.score_threshold_moderate:
                severities.append("moderate")
            else:
                severities.append("low")
        enriched_df["severity"] = severities

        # Metadata
        metadata = {
            "model_version": "1.0.0-isolation-forest",
            "model_name": "Marine Environmental Anomaly Detector (MEAD)",
            "algorithm": "IsolationForest",
            "dataset_name": dataset_name,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "sample_size": len(enriched_df),
            "anomaly_count": anomaly_count,
            "anomaly_rate_pct": anomaly_rate,
            "features_used": self.feature_engineer.selected_features,
            "hyperparameters": {
                "n_estimators": self.model_cfg.n_estimators,
                "contamination": self.model_cfg.contamination,
                "max_samples": str(self.model_cfg.max_samples),
                "random_state": self.model_cfg.random_state,
            },
            "score_normalization": {
                "score_min_raw": self.score_min_raw,
                "score_max_raw": self.score_max_raw,
            },
            "study_region": {
                "name": "Arabian Sea (Strict IHO S-23)",
                "standard": "IHO Publication S-23 (3rd Edition, Section 38: Arabian Sea)",
                "demarcation": {
                    "persian_gulf": "Excluded: lon <= 56.5°E and lat >= 23.5°N",
                    "gulf_of_oman": "Excluded: northwest of geodesic line Ras al Hadd (59.80°E, 22.53°N) -> Cape Jiwani (61.74°E, 25.02°N)",
                    "gulf_of_aden": "Excluded: west of geodesic line Ras Asir (51.28°E, 11.83°N) -> Ras Fartak (52.23°E, 15.63°N)",
                    "southern_boundary": "5.00°N",
                    "eastern_boundary": "78.00°E (Kanyakumari / Sri Lanka / Gulf of Mannar border)"
                }
            },
            "preprocessing_audit": audit.to_dict(),
            "temporal_range": {
                "start": str(enriched_df["timestamp"].min()),
                "end": str(enriched_df["timestamp"].max()),
            },
            "spatial_coverage": {
                "min_lat": float(enriched_df["latitude"].min()),
                "max_lat": float(enriched_df["latitude"].max()),
                "min_lon": float(enriched_df["longitude"].min()),
                "max_lon": float(enriched_df["longitude"].max()),
            },
            "sst_range_celsius": {
                "min": float(enriched_df["analysed_sst"].min()),
                "max": float(enriched_df["analysed_sst"].max()),
                "mean": round(float(enriched_df["analysed_sst"].mean()), 2),
            },
            "sst_anomaly_range": {
                "min": float(enriched_df["sst_anomaly"].min()),
                "max": float(enriched_df["sst_anomaly"].max()),
                "mean": round(float(enriched_df["sst_anomaly"].mean()), 3),
                "std": round(float(enriched_df["sst_anomaly"].std()), 3),
            },
            "scientific_limitations": [
                "Unsupervised anomaly detection: predictions denote statistical deviation from seasonal expectations, not biological mortality.",
                "Baselines represent spatial-monthly empirical averages derived from the observation window (short-term climatology proxy).",
                "Severe thermal anomalies require validation against in-situ buoys and coral reef thermal stress indices.",
            ],
        }

        logger.info(
            f"Training successful! Flagged {anomaly_count:,} anomalies ({anomaly_rate}% rate) "
            f"across {len(enriched_df):,} observations."
        )
        return enriched_df, metadata

    def fit_evaluate_chronological(
        self,
        train_raw_df: pd.DataFrame,
        test_raw_df: pd.DataFrame,
        dataset_name: str = "cmems_glorys12v1_arabian_sea_2024_2025",
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        """
        Executes leak-free chronological training & evaluation:
        - Train on 2024 observations
        - Test & evaluate on 2025 observations
        - Baselines fitted strictly on 2024 (zero 2025 leakage)
        """
        logger.info(
            f"Starting chronological train/test pipeline: "
            f"Train={len(train_raw_df):,} raw, Test={len(test_raw_df):,} raw..."
        )

        # 1. Preprocessing
        clean_train_df, train_audit = self.preprocessor.fit_transform(train_raw_df)
        clean_test_df, test_audit = self.preprocessor.transform(test_raw_df)

        if len(clean_train_df) == 0:
            raise ValueError("All training records were filtered out during preprocessing.")
        if len(clean_test_df) == 0:
            raise ValueError("All testing records were filtered out during preprocessing.")

        # 2. SST Climatological/Seasonal Baseline (FIT ON TRAIN ONLY)
        logger.info("Computing empirical SST seasonal-spatial baseline on 2024 training observations...")
        self.baseline_calc.fit(clean_train_df)
        clean_train_df = self.baseline_calc.transform(clean_train_df)
        clean_test_df = self.baseline_calc.transform(clean_test_df)

        # 3. Feature Engineering (FIT ON TRAIN ONLY)
        logger.info("Engineering environmental features (cyclic time, anomalies)...")
        enriched_train, X_train = self.feature_engineer.fit(clean_train_df).transform(clean_train_df)
        enriched_test, X_test = self.feature_engineer.transform(clean_test_df)

        # 4. Fit Isolation Forest on 2024
        logger.info(
            f"Fitting Isolation Forest on {len(X_train):,} training observations "
            f"with {len(self.feature_engineer.selected_features)} features: {self.feature_engineer.selected_features}..."
        )
        self.model.fit(X_train)
        self.is_fitted = True

        # 5. Score Normalization calibration from Train
        raw_train_scores = self.model.decision_function(X_train)
        self.score_min_raw = float(np.min(raw_train_scores))
        self.score_max_raw = float(np.max(raw_train_scores))
        score_range = max(self.score_max_raw - self.score_min_raw, 1e-6)

        # Predict on Test (2025)
        raw_test_scores = self.model.decision_function(X_test)
        labels_test = self.model.predict(X_test)
        norm_scores_test = np.clip(
            ((self.score_max_raw - raw_test_scores) / score_range) * 100.0, 0.0, 100.0
        ).round(2)
        is_anom_test = (labels_test == -1)

        enriched_test["anomaly_label"] = labels_test
        enriched_test["is_anomaly"] = is_anom_test
        enriched_test["anomaly_score"] = norm_scores_test
        enriched_test["raw_decision_score"] = raw_test_scores.round(4)

        # Severity classification for test
        severities = []
        anomaly_types = []
        for s, anom, sst_a in zip(norm_scores_test, is_anom_test, enriched_test["sst_anomaly"]):
            if s >= self.model_cfg.score_threshold_critical:
                severities.append("critical")
            elif s >= self.model_cfg.score_threshold_high:
                severities.append("high")
            elif s >= self.model_cfg.score_threshold_moderate:
                severities.append("moderate")
            else:
                severities.append("low")

            if anom:
                if sst_a > 0:
                    anomaly_types.append("Marine Heatwave (MHW)")
                else:
                    anomaly_types.append("Severe Cold Upwelling Surge")
            else:
                anomaly_types.append("Normal Environmental State")

        enriched_test["severity"] = severities
        enriched_test["anomaly_type"] = anomaly_types

        # Also predict on train
        norm_scores_train = np.clip(
            ((self.score_max_raw - raw_train_scores) / score_range) * 100.0, 0.0, 100.0
        ).round(2)
        labels_train = self.model.predict(X_train)
        enriched_train["anomaly_label"] = labels_train
        enriched_train["is_anomaly"] = (labels_train == -1)
        enriched_train["anomaly_score"] = norm_scores_train
        enriched_train["raw_decision_score"] = raw_train_scores.round(4)

        anom_count_test = int(np.sum(is_anom_test))
        anom_rate_test = round(float(anom_count_test / len(enriched_test) * 100), 2)

        metadata = {
            "model_version": "1.0.0-isolation-forest-production",
            "model_name": "Marine Environmental Anomaly Detector (MEAD)",
            "algorithm": "IsolationForest",
            "dataset_name": dataset_name,
            "data_source": "REAL Copernicus Marine Service (CMEMS) GLORYS12V1 Physics Reanalysis",
            "is_real_data": True,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "evaluation_strategy": "Chronological Out-of-Time Validation (Train: 2024, Test: 2025)",
            "sample_size": {
                "train_observations": len(enriched_train),
                "test_observations": len(enriched_test),
                "total_observations": len(enriched_train) + len(enriched_test),
            },
            "test_results": {
                "anomaly_count": anom_count_test,
                "anomaly_rate_pct": anom_rate_test,
                "mhw_count": int(np.sum(enriched_test["anomaly_type"] == "Marine Heatwave (MHW)")),
                "cold_surge_count": int(np.sum(enriched_test["anomaly_type"] == "Severe Cold Upwelling Surge")),
            },
            "features_used": self.feature_engineer.selected_features,
            "hyperparameters": {
                "n_estimators": self.model_cfg.n_estimators,
                "contamination": self.model_cfg.contamination,
                "contamination_rationale": "0.03 (3.0%): In marine climatology (Hobday et al. 2016), discrete extreme thermal anomalies represent the upper/lower tails beyond the 97th percentile of normal seasonal variation.",
                "max_samples": str(self.model_cfg.max_samples),
                "random_state": self.model_cfg.random_state,
                "n_jobs": self.model_cfg.n_jobs,
            },
            "score_normalization": {
                "score_min_raw": self.score_min_raw,
                "score_max_raw": self.score_max_raw,
            },
            "study_region": {
                "name": "Arabian Sea (Strict IHO S-23)",
                "standard": "IHO Publication S-23 (3rd Edition, Section 38: Arabian Sea)",
                "demarcation": {
                    "persian_gulf": "Excluded: lon <= 56.5°E and lat >= 23.5°N",
                    "gulf_of_oman": "Excluded: northwest of geodesic line Ras al Hadd (59.80°E, 22.53°N) -> Cape Jiwani (61.74°E, 25.02°N)",
                    "gulf_of_aden": "Excluded: west of geodesic line Ras Asir (51.28°E, 11.83°N) -> Ras Fartak (52.23°E, 15.63°N)",
                    "southern_boundary": "5.00°N",
                    "eastern_boundary": "78.00°E (Kanyakumari / Sri Lanka / Gulf of Mannar border)"
                }
            },
            "preprocessing_audit_train": train_audit.to_dict(),
            "preprocessing_audit_test": test_audit.to_dict(),
            "temporal_range": {
                "train_start": str(enriched_train["timestamp"].min()),
                "train_end": str(enriched_train["timestamp"].max()),
                "test_start": str(enriched_test["timestamp"].min()),
                "test_end": str(enriched_test["timestamp"].max()),
            },
            "spatial_coverage": {
                "min_lat": float(enriched_test["latitude"].min()),
                "max_lat": float(enriched_test["latitude"].max()),
                "min_lon": float(enriched_test["longitude"].min()),
                "max_lon": float(enriched_test["longitude"].max()),
            },
            "sst_range_celsius_test": {
                "min": float(enriched_test["analysed_sst"].min()),
                "max": float(enriched_test["analysed_sst"].max()),
                "mean": round(float(enriched_test["analysed_sst"].mean()), 2),
            },
            "sst_anomaly_range_test": {
                "min": float(enriched_test["sst_anomaly"].min()),
                "max": float(enriched_test["sst_anomaly"].max()),
                "mean": round(float(enriched_test["sst_anomaly"].mean()), 3),
                "std": round(float(enriched_test["sst_anomaly"].std()), 3),
            },
            "scientific_limitations": [
                "Unsupervised anomaly detection: predictions denote statistical deviation from seasonal expectations, not biological mortality.",
                "Baselines represent spatial-monthly empirical averages derived from the 2024 observation window (climatology proxy).",
                "Severe thermal anomalies require validation against in-situ buoys and coral reef thermal stress indices.",
            ],
        }

        logger.info(
            f"Chronological evaluation successful! Test flagged {anom_count_test:,} anomalies ({anom_rate_test}% rate) "
            f"across {len(enriched_test):,} out-of-time 2025 observations."
        )
        return enriched_test, metadata, enriched_train

    def save_artifacts(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Saves trained model, baseline calculator, and configuration to disk."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before saving artifacts.")

        target_dir = Path(output_dir or self.config.models_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save Isolation Forest model
        joblib.dump(self.model, target_dir / "isolation_forest.joblib")

        # 2. Save Baseline Calculator
        with open(target_dir / "baseline_calculator.json", "w", encoding="utf-8") as f:
            json.dump(self.baseline_calc.to_dict(), f, indent=2)

        # 3. Save Feature Engineer Config
        feature_cfg = {
            "selected_features": self.feature_engineer.selected_features,
            "score_normalization": {
                "score_min_raw": self.score_min_raw,
                "score_max_raw": self.score_max_raw,
            },
            "severity_thresholds": {
                "moderate": self.model_cfg.score_threshold_moderate,
                "high": self.model_cfg.score_threshold_high,
                "critical": self.model_cfg.score_threshold_critical,
            },
            "use_cyclic_time": self.config.use_cyclic_time,
        }
        with open(target_dir / "feature_config.json", "w", encoding="utf-8") as f:
            json.dump(feature_cfg, f, indent=2)

        # 4. Save Master Metadata
        if metadata:
            with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        logger.info(f"Environmental anomaly artifacts successfully saved to {target_dir}")
