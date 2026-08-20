"""
Test Deferred Scientific Endpoints (Phase 6 Correlation, Phase 7 Otolith, Phase 8 ML).
Verifies that un-implemented scientific phases return standard 501 responses without fabricating results.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_otolith_analyse_returns_501(monkeypatch):
    """POST /api/v1/otolith/analyse returns 501 when sample exists without fabricating CV annuli analysis."""
    from backend.app.db.database import execute_single
    monkeypatch.setattr("backend.app.api.v1.otolith.execute_single", lambda q, p: {"id": "sample-01"})
    
    response = client.post("/api/v1/otolith/analyse?sample_id=sample-01")
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "OTOLITH_MODULE_PENDING"


def test_correlation_returns_501():
    """POST /api/v1/analysis/correlation returns 501 without fabricating correlation stats."""
    response = client.post(
        "/api/v1/analysis/correlation",
        json={"variable_x": "temperature", "variable_y": "catch_weight_kg"}
    )
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "ANALYSIS_MODULE_PENDING"


def test_ml_predict_returns_501():
    """POST /api/v1/ml/predict returns 501 without fabricating fake linear equations."""
    response = client.post(
        "/api/v1/ml/predict",
        json={"model_id": "sst-catch-predictor-v1", "features": {"temperature": 28.5}}
    )
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "ML_MODULE_PENDING"


def test_validation_error_format():
    """Invalid input payload produces standard JSON error envelope with VALIDATION_ERROR code."""
    response = client.post(
        "/api/v1/marine/query",
        json={"page": -5}  # Invalid page (< 1)
    )
    assert response.status_code == 422
    err = response.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
