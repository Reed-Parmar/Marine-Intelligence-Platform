"""
Phase 14.3 Fisheries Catch Prediction V1 Module.
Encapsulates tuned XGBoost regression model targeting TotalCatchMT.
Preserves exact V1 feature engineering and preprocessing.
"""
from .pipeline import (
    ALL_INPUT_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    assign_monsoon,
    engineer_features,
)
from .predict import (
    DEFAULT_MODEL_DIR,
    FisheriesCatchPredictor,
    get_fisheries_predictor,
    predict_catch,
)

__all__ = [
    "ALL_INPUT_FEATURES",
    "CATEGORICAL_FEATURES",
    "NUMERICAL_FEATURES",
    "assign_monsoon",
    "engineer_features",
    "DEFAULT_MODEL_DIR",
    "FisheriesCatchPredictor",
    "get_fisheries_predictor",
    "predict_catch",
]
