import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data paths
# Adjusting to the actual path where the user placed it
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DATA_FILE = os.path.join(DATA_DIR, "iotc_2023_2024.csv")

# Artifacts paths
ARTIFACTS_DIR = BASE_DIR
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "xgboost_model.json")
PREPROCESSING_PATH = os.path.join(ARTIFACTS_DIR, "preprocessing.joblib")
METRICS_PATH = os.path.join(ARTIFACTS_DIR, "metrics.json")
FEATURE_IMPORTANCE_PATH = os.path.join(ARTIFACTS_DIR, "feature_importance.csv")
PREDICTIONS_PATH = os.path.join(ARTIFACTS_DIR, "predictions.csv")

# XGBoost Parameters
XGB_PARAMS = {
    "n_estimators": 300,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "n_jobs": -1
}

# Features
FEATURES = [
    "MONTH",
    "SPECIES",
    "FLEET",
    "FISHERY",
    "GEAR",
    "FISHING_GROUND_CODE",
    "FISHING_DAYS"
]
TARGET = "CATCH"
