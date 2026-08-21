"""
Test Scientific Endpoints (Phase 6 Correlation, Phase 7 Otolith, Phase 8 ML).
Verifies that Phase 6 and Phase 7 integrate real scientific engines, and Phase 8 ML remains cleanly deferred.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_otolith_analyse_returns_200(monkeypatch):
    """POST /api/v1/otolith/analyse runs Phase 7 deterministic otolith analysis engine."""
    monkeypatch.setattr("backend.app.api.v1.otolith.execute_single", lambda q, p: {"id": "sample-01", "fish_length_cm": 25.0})
    
    response = client.post("/api/v1/otolith/analyse?sample_id=sample-01")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["sample_id"] == "sample-01"
    assert data["status"] in ["identified", "provisional", "completed"]
    assert "confidence_score" in data
    assert "estimated_age_years" in data
    assert "morphological_features" in data


def test_correlation_returns_200(monkeypatch):
    """POST /api/v1/analysis/correlation runs Phase 6 deterministic cross-domain correlation engine."""
    response = client.post(
        "/api/v1/analysis/correlation",
        json={"variable_x": "temperature", "variable_y": "catch_weight_kg"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["variable_x"] == "temperature"
    assert data["variable_y"] == "catch_weight_kg"
    assert "statistics" in data
    assert "interpretation" in data


def test_ml_predict_returns_501():
    """POST /api/v1/ml/predict returns 501 without fabricating fake linear equations."""
    response = client.post(
        "/api/v1/ml/predict",
        json={"model_id": "sst-catch-predictor-v1", "features": {"temperature": 28.5}}
    )
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "ML_MODULE_PENDING"


def test_dataset_preview_endpoint(monkeypatch):
    """GET /api/v1/datasets/{id}/preview returns tabular preview."""
    from backend.app.services.dataset_service import DatasetService
    from backend.app.schemas.dataset import DatasetPreviewResponse, DatasetResponse

    monkeypatch.setattr(
        DatasetService,
        "get_dataset_by_id",
        lambda did: DatasetResponse(id=did, name="CMLRE CTD Cast", domain_type="oceanography")
    )
    monkeypatch.setattr("backend.app.api.v1.datasets.get_current_user", lambda: None)

    response = client.get("/api/v1/datasets/ds-test-01/preview")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["dataset_id"] == "ds-test-01"
    assert "columns" in data
    assert "rows" in data


def test_marine_location_detail_endpoint():
    """GET /api/v1/marine/location-detail returns fused cross-domain environmental and biological context."""
    response = client.get("/api/v1/marine/location-detail?lat=10.0&lon=75.5")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "coordinates" in data
    assert "oceanography" in data
    assert "fisheries" in data
    assert "biodiversity" in data
    assert "molecularEdna" in data


def test_ocean_ctd_profile_endpoint():
    """GET /api/v1/ocean/ctd-profile returns vertical hydrographic casts."""
    response = client.get("/api/v1/ocean/ctd-profile?station_id=STN-01")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) > 0
    assert "depth" in data[0]
    assert "temperature" in data[0]
    assert "salinity" in data[0]


def test_validation_error_format():
    """Invalid input payload produces standard JSON error envelope with VALIDATION_ERROR code."""
    response = client.post(
        "/api/v1/marine/query",
        json={"page": -5}  # Invalid page (< 1)
    )
    assert response.status_code == 422
    err = response.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
