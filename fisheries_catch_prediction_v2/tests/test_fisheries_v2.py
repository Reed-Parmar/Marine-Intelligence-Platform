"""
Pytest test suite for Fisheries Catch Prediction V2.
Tests feature engineering, inference engine, input validation, and FastAPI endpoints.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fisheries_catch_prediction_v2.src.features_v2 import (
    assign_monsoon,
    assign_region,
    engineer_features_v2,
    ALL_FEATURES_V2,
    ALL_CATEGORICAL_V2
)
from fisheries_catch_prediction_v2.src.pipeline_v2 import build_preprocessor_v2, calculate_metrics
from fisheries_catch_prediction_v2.src.predict_v2 import FisheriesCatchPredictorV2, predict_catch_v2
from fisheries_catch_prediction_v2.api.main import app


@pytest.fixture(scope="session")
def predictor_v2():
    return FisheriesCatchPredictorV2()


@pytest.fixture(scope="session")
def client_v2():
    with TestClient(app) as client:
        yield client


# 1. Feature Engineering Tests
def test_v2_monsoon_assignment():
    assert assign_monsoon(1) == "NE_Monsoon"
    assert assign_monsoon(4) == "Intermonsoon_Spring"
    assert assign_monsoon(7) == "SW_Monsoon"
    assert assign_monsoon(10) == "Intermonsoon_Autumn"


def test_v2_region_assignment():
    assert assign_region(12.5, 62.5) == "Arabian_Sea"
    assert assign_region(12.5, 85.0) == "Bay_of_Bengal"
    assert assign_region(0.0, 50.0) == "Western_Equatorial"
    assert assign_region(-2.0, 90.0) == "Eastern_Equatorial"
    assert assign_region(-15.0, 42.0) == "Mozambique_Channel"
    assert assign_region(-25.0, 70.0) == "Southern_Indian_Ocean"


def test_v2_engineer_features():
    df = pd.DataFrame([{
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 40.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2022,
        "Latitude": 12.5,
        "Longitude": 62.5
    }])
    df_feat = engineer_features_v2(df)

    assert "Fleet_x_Gear" in df_feat.columns
    assert "Location_x_Season" in df_feat.columns
    assert "Region" in df_feat.columns
    assert df_feat["Region"].iloc[0] == "Arabian_Sea"
    assert df_feat["MonsoonSeason"].iloc[0] == "SW_Monsoon"
    assert df_feat["Fleet_x_Gear"].iloc[0] == "EUESP_PS"
    assert df_feat["Location_x_Season"].iloc[0] == "Arabian_Sea_SW_Monsoon"


# 2. Pipeline & Metrics Tests
def test_v2_preprocessor_transformation():
    df = pd.DataFrame([{
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 20.0,
        "EffortUnits": "FHOURS",
        "Month": 6,
        "Year": 2021,
        "Latitude": 10.0,
        "Longitude": 60.0
    }])
    df_feat = engineer_features_v2(df)
    pre = build_preprocessor_v2()
    X_t = pre.fit_transform(df_feat[ALL_FEATURES_V2])
    assert X_t.shape[0] == 1
    assert not np.isnan(X_t).any()


def test_v2_calculate_metrics():
    y_true = np.array([50.0, 100.0, 0.0])
    y_pred = np.array([45.0, 110.0, 5.0])
    met = calculate_metrics(y_true, y_pred)
    assert met["MAE"] == pytest.approx(6.666, 0.01)
    assert met["R2"] > 0.90
    assert not np.isnan(met["sMAPE"])


# 3. Predictor Tests
def test_v2_artifacts_exist(predictor_v2):
    assert os.path.exists(predictor_v2.preprocessor_path)
    assert os.path.exists(predictor_v2.model_path)
    assert os.path.exists(predictor_v2.metadata_path)
    assert predictor_v2.model is not None


def test_v2_single_prediction(predictor_v2):
    sample = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 45.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2022,
        "Latitude": 12.5,
        "Longitude": 62.5
    }
    res = predictor_v2.predict(sample)
    assert isinstance(res, dict)
    assert "predicted_catch_mt" in res
    assert res["predicted_catch_mt"] >= 0.0
    assert res["unit"] == "Metric Tons (MT)"
    assert res["version"] == "2.0.0"


def test_v2_batch_prediction(predictor_v2):
    batch = [
        {"Fleet": "EUESP", "Gear": "PS", "Effort": 40.0, "EffortUnits": "FHOURS", "Month": 8, "Year": 2022, "Latitude": 12.5, "Longitude": 62.5},
        {"Fleet": "MDV", "Gear": "BB", "Effort": 20.0, "EffortUnits": "FDAYS", "Month": 11, "Year": 2021, "Latitude": 2.0, "Longitude": 73.0}
    ]
    preds = predictor_v2.predict_batch(batch)
    assert len(preds) == 2
    for p in preds:
        assert p["predicted_catch_mt"] >= 0.0


def test_v2_invalid_inputs(predictor_v2):
    # Missing Effort
    with pytest.raises(ValueError, match="missing required fisheries columns"):
        predictor_v2.predict({"Fleet": "EUESP", "Gear": "PS", "Month": 8, "Year": 2022, "Latitude": 12.5, "Longitude": 62.5})

    # Out of range month
    with pytest.raises(ValueError, match="Month values must be integers between 1 and 12"):
        predictor_v2.predict({"Fleet": "EUESP", "Gear": "PS", "Effort": 10.0, "EffortUnits": "FHOURS", "Month": 13, "Year": 2022, "Latitude": 12.5, "Longitude": 62.5})


# 4. FastAPI Tests
def test_v2_api_health(client_v2):
    res = client_v2.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["version"] == "2.0.0"


def test_v2_api_model_info(client_v2):
    res = client_v2.get("/model-info")
    assert res.status_code == 200
    data = res.json()
    assert "metadata" in data
    assert "feature_schema" in data


def test_v2_api_predict(client_v2):
    payload = {
        "Fleet": "EUESP",
        "Gear": "PS",
        "Effort": 45.0,
        "EffortUnits": "FHOURS",
        "Month": 8,
        "Year": 2022,
        "Latitude": 12.5,
        "Longitude": 62.5
    }
    res = client_v2.post("/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["predicted_catch"] >= 0.0
    assert data["unit"] == "Metric Tons (MT)"
    assert data["version"] == "2.0.0"


def test_v2_api_batch_predict(client_v2):
    payload = {
        "items": [
            {"Fleet": "EUESP", "Gear": "PS", "Effort": 45.0, "EffortUnits": "FHOURS", "Month": 8, "Year": 2022, "Latitude": 12.5, "Longitude": 62.5},
            {"Fleet": "MDV", "Gear": "BB", "Effort": 15.0, "EffortUnits": "FDAYS", "Month": 11, "Year": 2021, "Latitude": 2.0, "Longitude": 73.0}
        ]
    }
    res = client_v2.post("/predict/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 2
