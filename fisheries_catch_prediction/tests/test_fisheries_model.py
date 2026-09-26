"""
Comprehensive test suite for Fisheries Catch Prediction (Phase 14.3).
Covers:
- Preprocessing and ColumnTransformer transformations
- Feature engineering (monsoons, cyclic features, log effort)
- Model loading and persistence verification
- Deterministic inference
- Single and batch predictions
- Output schema, non-negativity, and NaN-freedom
- Invalid input validation handling
- FastAPI endpoints (/health, /model-info, /predict, /predict/batch)
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fisheries_catch_prediction.src.pipeline import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    ALL_INPUT_FEATURES,
    engineer_features,
    build_preprocessor,
    assign_monsoon,
    calculate_metrics
)
from fisheries_catch_prediction.src.predict import FisheriesCatchPredictor, predict_catch
from fisheries_catch_prediction.api.main import app


@pytest.fixture(scope="session")
def predictor():
    """Session fixture loading predictor."""
    return FisheriesCatchPredictor()


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as c:
        yield c


# 1. Feature Engineering Tests
def test_monsoon_assignment():
    assert assign_monsoon(12) == "NE_Monsoon"
    assert assign_monsoon(1) == "NE_Monsoon"
    assert assign_monsoon(4) == "Intermonsoon_Spring"
    assert assign_monsoon(7) == "SW_Monsoon"
    assert assign_monsoon(10) == "Intermonsoon_Autumn"


def test_engineer_features():
    df_raw = pd.DataFrame([{
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 25.0,
        "EffortUnits": "FHOURS",
        "Month": 6,
        "Year": 2021,
        "Latitude": 10.5,
        "Longitude": 60.5
    }])
    df_feat = engineer_features(df_raw)

    assert "Month_Sin" in df_feat.columns
    assert "Month_Cos" in df_feat.columns
    assert "Quarter" in df_feat.columns
    assert "MonsoonSeason" in df_feat.columns
    assert "Log_Effort" in df_feat.columns
    assert df_feat["Quarter"].iloc[0] == 2
    assert df_feat["MonsoonSeason"].iloc[0] == "SW_Monsoon"
    assert np.isclose(df_feat["Log_Effort"].iloc[0], np.log1p(25.0))


# 2. Preprocessing Tests
def test_preprocessor_transformation(predictor):
    df_test = pd.DataFrame([{
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 20.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2020,
        "Latitude": 5.0,
        "Longitude": 55.0
    }])
    df_feat = engineer_features(df_test)
    X_trans = predictor.preprocessor.transform(df_feat[ALL_INPUT_FEATURES])

    assert X_trans.shape[0] == 1
    assert X_trans.shape[1] == 48  # 48 encoded features
    assert not np.isnan(X_trans).any()


def test_unseen_categorical_handling(predictor):
    """Ensure handle_unknown='ignore' prevents crashes on novel unseen flags/gears."""
    df_unseen = pd.DataFrame([{
        "Fleet": "UNKNOWN_COUNTRY",
        "Gear": "UNKNOWN_GEAR",
        "Effort": 15.0,
        "EffortUnits": "FHOURS",
        "Month": 3,
        "Year": 2025,
        "Latitude": 12.0,
        "Longitude": 65.0
    }])
    df_feat = engineer_features(df_unseen)
    X_trans = predictor.preprocessor.transform(df_feat[ALL_INPUT_FEATURES])
    assert X_trans.shape[0] == 1
    assert not np.isnan(X_trans).any()


# 3. Model Loading & Metadata Tests
def test_model_artifacts_exist(predictor):
    assert os.path.exists(predictor.preprocessor_path)
    assert os.path.exists(predictor.metadata_path)
    assert os.path.exists(predictor.schema_path)
    assert predictor.model is not None


def test_model_metadata_content(predictor):
    meta = predictor.metadata
    assert meta["model_name"] == "IOTC Surface Fisheries Catch Predictor"
    assert "xgboost" in meta["training_framework"].lower()
    assert meta["target"] == "TotalCatchMT"
    assert "best_hyperparameters" in meta
    assert "final_test_metrics" in meta
    assert meta["final_test_metrics"]["R2"] > 0.50


# 4. Single & Batch Inference Tests
def test_single_prediction(predictor):
    input_data = {
        "Fleet": "EUFRA",
        "Gear": "PS",
        "Effort": 35.0,
        "EffortUnits": "FHOURS",
        "Month": 10,
        "Year": 2021,
        "Latitude": 3.5,
        "Longitude": 58.5
    }
    res = predictor.predict(input_data)

    assert isinstance(res, dict)
    assert "predicted_catch_mt" in res
    assert isinstance(res["predicted_catch_mt"], float)
    assert res["predicted_catch_mt"] >= 0.0
    assert not np.isnan(res["predicted_catch_mt"])
    assert res["unit"] == "Metric Tons (MT)"


def test_batch_prediction(predictor):
    batch = [
        {"Fleet": "EUESP", "Gear": "PS", "Effort": 20.0, "EffortUnits": "FHOURS", "Month": 4, "Year": 2021, "Latitude": 0.0, "Longitude": 50.0},
        {"Fleet": "MDV", "Gear": "BB", "Effort": 10.0, "EffortUnits": "FDAYS", "Month": 8, "Year": 2020, "Latitude": 4.0, "Longitude": 73.0},
        {"Fleet": "SYC", "Gear": "PS", "Effort": 50.0, "EffortUnits": "FHOURS", "Month": 1, "Year": 2022, "Latitude": -2.0, "Longitude": 60.0}
    ]
    preds = predictor.predict_batch(batch)

    assert isinstance(preds, list)
    assert len(preds) == 3
    for p in preds:
        assert p["predicted_catch_mt"] >= 0.0
        assert not np.isnan(p["predicted_catch_mt"])
        assert p["unit"] == "Metric Tons (MT)"


def test_deterministic_inference(predictor):
    sample = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 40.0,
        "EffortUnits": "FHOURS",
        "Month": 7,
        "Year": 2022,
        "Latitude": 5.5,
        "Longitude": 52.5
    }
    p1 = predictor.predict(sample)["predicted_catch_mt"]
    p2 = predictor.predict(sample)["predicted_catch_mt"]
    assert p1 == p2


# 5. Invalid Input Validation Tests
def test_missing_required_column(predictor):
    invalid = {
        "Fleet": "EUESP",
        "Gear": "PS",
        # Effort missing
        "EffortUnits": "FHOURS",
        "Month": 7,
        "Year": 2022,
        "Latitude": 5.5,
        "Longitude": 52.5
    }
    with pytest.raises(ValueError, match="missing required fisheries columns"):
        predictor.predict(invalid)


def test_invalid_month_range(predictor):
    invalid = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 10.0,
        "EffortUnits": "FHOURS",
        "Month": 14,  # Invalid month
        "Year": 2022,
        "Latitude": 5.5,
        "Longitude": 52.5
    }
    with pytest.raises(ValueError, match="Month values must be integers between 1 and 12"):
        predictor.predict(invalid)


def test_negative_effort(predictor):
    invalid = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": -15.0,  # Negative effort
        "EffortUnits": "FHOURS",
        "Month": 5,
        "Year": 2022,
        "Latitude": 5.5,
        "Longitude": 52.5
    }
    with pytest.raises(ValueError, match="Fishing effort cannot be negative"):
        predictor.predict(invalid)


# 6. Metrics Calculation Tests
def test_calculate_metrics():
    y_true = np.array([10.0, 20.0, 0.0, 50.0])
    y_pred = np.array([12.0, 18.0, 2.0, 45.0])
    m = calculate_metrics(y_true, y_pred)

    assert "MAE" in m
    assert "RMSE" in m
    assert "R2" in m
    assert "sMAPE" in m
    assert "Bias" in m
    assert m["MAE"] == pytest.approx(2.75, 0.01)
    assert not np.isnan(m["sMAPE"])
    assert not np.isinf(m["sMAPE"])


# 7. FastAPI Endpoint Tests
def test_api_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["target_unit"] == "Metric Tons (MT)"


def test_api_model_info(client):
    res = client.get("/model-info")
    assert res.status_code == 200
    data = res.json()
    assert "metadata" in data
    assert "feature_schema" in data


def test_api_predict_success(client):
    payload = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 45.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2022,
        "Latitude": 2.5,
        "Longitude": 55.5
    }
    res = client.post("/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_catch" in data
    assert data["predicted_catch"] >= 0.0
    assert data["unit"] == "Metric Tons (MT)"
    assert data["model"] == "XGBoost Regressor (Tuned)"


def test_api_predict_validation_error(client):
    # Invalid Month (13) and negative Effort (-5.0)
    payload = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": -5.0,
        "EffortUnits": "FHOURS",
        "Month": 13,
        "Year": 2022,
        "Latitude": 2.5,
        "Longitude": 55.5
    }
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_api_batch_predict_success(client):
    payload = {
        "items": [
            {"Fleet": "EUFRA", "Gear": "PS", "Effort": 30.0, "EffortUnits": "FHOURS", "Month": 5, "Year": 2022, "Latitude": 4.5, "Longitude": 52.0},
            {"Fleet": "MDV", "Gear": "BB", "Effort": 15.0, "EffortUnits": "FDAYS", "Month": 11, "Year": 2021, "Latitude": 1.0, "Longitude": 73.0}
        ]
    }
    res = client.post("/predict/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 2
    assert len(data["predictions"]) == 2
    for pred in data["predictions"]:
        assert pred["predicted_catch"] >= 0.0
