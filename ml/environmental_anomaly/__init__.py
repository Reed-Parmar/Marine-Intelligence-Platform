"""
Environmental Anomaly Detection ML Module.

Phase 14.1 of the CMLRE Marine Intelligence Platform.
"""

from .config import (
    AnomalyModelConfig,
    BaselineConfig,
    DATA_DIR,
    MODELS_DIR,
    PipelineConfig,
    RESULTS_DIR,
    default_config,
)
from .data_loader import DatasetInspectionReport, EnvironmentalDataLoader
from .evaluate import AnomalyEvaluationReport, EnvironmentalAnomalyEvaluator
from .feature_engineering import EnvironmentalFeatureEngineer, SSTBaselineCalculator
from .predict import (
    AnomalyPredictionResult,
    EnvironmentalAnomalyInferenceEngine,
    get_inference_engine,
    predict_environmental_anomaly,
)
from .preprocessing import EnvironmentalPreprocessor, PreprocessingAuditReport
from .train import EnvironmentalAnomalyTrainer
from .utils import (
    generate_diagnostic_plots,
    generate_synthetic_environmental_df,
    generate_synthetic_environmental_netcdf,
)

__all__ = [
    "PipelineConfig",
    "AnomalyModelConfig",
    "BaselineConfig",
    "DATA_DIR",
    "MODELS_DIR",
    "RESULTS_DIR",
    "default_config",
    "EnvironmentalDataLoader",
    "DatasetInspectionReport",
    "EnvironmentalPreprocessor",
    "PreprocessingAuditReport",
    "SSTBaselineCalculator",
    "EnvironmentalFeatureEngineer",
    "EnvironmentalAnomalyTrainer",
    "EnvironmentalAnomalyEvaluator",
    "AnomalyEvaluationReport",
    "EnvironmentalAnomalyInferenceEngine",
    "AnomalyPredictionResult",
    "get_inference_engine",
    "predict_environmental_anomaly",
    "generate_synthetic_environmental_netcdf",
    "generate_synthetic_environmental_df",
    "generate_diagnostic_plots",
]
