"""
API Integration Tests for Seasonal Species Distribution Shift Endpoint.

Verifies:
1. Valid request execution for Indian Oil Sardine (Sardinella longiceps).
2. Distinct source_season and target_season calculation across monsoon regimes.
3. Successful inference with all environmental CTD inputs provided.
4. Successful inference with missing environmental inputs (null).
5. 404 response for unknown marine species.
6. 400/422 response for invalid ecological sectors.
7. 400/422 response for out-of-bounds geographic coordinates.
8. 422 validation failure for invalid month (e.g. month=13).
9. 422 validation failure for invalid forecast horizon (e.g. delta_t=0 or 15).
10. Probability distribution sum equals 1.0.
11. Top-3 predictions ranked strictly descending by probability.
12. Scientific limitations and terminology present in response payload.
"""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_01_valid_prediction_indian_oil_sardine():
    """1. Valid request for Indian Oil Sardine returns 200 and structured prediction."""
    payload = {
        "species_id": "Sardinella longiceps",
        "current_sector": "Malabar Upwelling Shelf",
        "latitude": 10.5,
        "longitude": 75.5,
        "month": 4,
        "forecast_horizon_months": 2,
        "mean_depth_meters": 35.0,
        "sst_celsius": 29.5,
        "salinity_psu": 35.2,
        "dissolved_oxygen_mgl": 4.8,
        "chlorophyll_mg_m3": 1.5,
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code == 200, f"Expected 200, got: {response.text}"

    data = response.json()
    assert data["species"] == "Sardinella longiceps"
    assert data["prediction_type"] == "seasonal_distribution_shift"
    assert data["source_sector"] == "Malabar Upwelling Shelf"
    assert data["forecast_horizon_months"] == 2
    assert "top_prediction" in data
    assert "top_3_predictions" in data
    assert "probability_distribution" in data
    assert "confidence_level" in data
    assert "confidence_tier" in data
    assert data["environmental_context_available"] is True
    assert "markov_baseline_comparison" in data
    assert "limitations" in data

    # Probabilities sum to 1.0
    prob_sum = sum(data["probability_distribution"].values())
    assert pytest.approx(prob_sum, 0.001) == 1.0

    # Top-3 sorted descending
    top_3 = data["top_3_predictions"]
    assert len(top_3) == 3
    assert top_3[0]["probability"] >= top_3[1]["probability"]
    assert top_3[1]["probability"] >= top_3[2]["probability"]


def test_02_distinct_source_and_target_seasons():
    """2. Verifies distinct source_season and target_season calculation (Month 4 Pre-Monsoon -> Month 6 SW Monsoon)."""
    payload = {
        "species_id": "Sardinella longiceps",
        "current_sector": "Malabar Upwelling Shelf",
        "latitude": 10.5,
        "longitude": 75.5,
        "month": 4,  # April (Pre-Monsoon, code 1)
        "forecast_horizon_months": 2,  # June (SW Monsoon, code 2)
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    forecast = data["forecast"]
    assert forecast["source_month"] == 4
    assert forecast["target_month"] == 6
    assert forecast["source_season"]["season_code"] == 1
    assert "Pre-Monsoon" in forecast["source_season"]["season_name"]
    assert forecast["target_season"]["season_code"] == 2
    assert "SW Monsoon" in forecast["target_season"]["season_name"]


def test_03_missing_environmental_inputs():
    """3. Verifies prediction executes smoothly when optional sensor measurements are null/omitted."""
    payload = {
        "species_id": "Rastrelliger kanagurta",
        "current_sector": "Konkan Coast / Central West Coast",
        "latitude": 15.5,
        "longitude": 73.2,
        "month": 7,
        "forecast_horizon_months": 3,
        "sst_celsius": None,
        "salinity_psu": None,
        "dissolved_oxygen_mgl": None,
        "chlorophyll_mg_m3": None,
        "mean_depth_meters": None,
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["environmental_context_available"] is False
    assert data["environmental_inputs"]["sst_celsius"] is None
    assert len(data["top_3_predictions"]) == 3
    assert pytest.approx(sum(data["probability_distribution"].values()), 0.001) == 1.0


def test_04_unknown_species_returns_404():
    """4. Verifies unrecognized species raises 404 with descriptive error."""
    payload = {
        "species_id": "Imaginary_DeepSea_Creature_XYZ",
        "current_sector": "Malabar Upwelling Shelf",
        "latitude": 10.5,
        "longitude": 75.5,
        "month": 5,
        "forecast_horizon_months": 2,
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code == 404
    data = response.json()
    err_msg = data.get("error", {}).get("message") or data.get("detail", "")
    assert "not in the trained species vocabulary" in err_msg


def test_05_invalid_sector_returns_400_or_422():
    """5. Verifies invalid sector name raises 400 or 422 error."""
    payload = {
        "species_id": "Sardinella longiceps",
        "current_sector": "Pacific_Northwest_Ridge",
        "latitude": 10.5,
        "longitude": 75.5,
        "month": 5,
        "forecast_horizon_months": 2,
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code in (400, 422)


def test_06_invalid_coordinates_returns_422():
    """6. Verifies coordinates outside Arabian Sea boundary are rejected."""
    payload = {
        "species_id": "Sardinella longiceps",
        "current_sector": "Malabar Upwelling Shelf",
        "latitude": 45.0,  # Far north outside Arabian Sea (max 24.0°N)
        "longitude": 75.5,
        "month": 5,
        "forecast_horizon_months": 2,
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code in (400, 422)


def test_07_invalid_month_returns_422():
    """7. Verifies month outside 1-12 range fails Pydantic validation with 422."""
    payload = {
        "species_id": "Sardinella longiceps",
        "current_sector": "Malabar Upwelling Shelf",
        "latitude": 10.5,
        "longitude": 75.5,
        "month": 13,  # Invalid month
        "forecast_horizon_months": 2,
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code == 422


def test_08_invalid_forecast_horizon_returns_422():
    """8. Verifies forecast horizon outside 1-11 range fails Pydantic validation with 422."""
    payload = {
        "species_id": "Sardinella longiceps",
        "current_sector": "Malabar Upwelling Shelf",
        "latitude": 10.5,
        "longitude": 75.5,
        "month": 4,
        "forecast_horizon_months": 0,  # Invalid horizon (< 1)
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code == 422


def test_09_scientific_limitations_and_disclaimer():
    """9. Verifies output explicitly includes scientific limitations and non-telemetry disclaimers."""
    payload = {
        "species_id": "Stolephorus indicus",
        "current_sector": "Wadge Bank / Comorin Sector",
        "latitude": 7.5,
        "longitude": 77.5,
        "month": 10,
        "forecast_horizon_months": 2,
    }

    response = client.post("/api/v1/distribution-shift/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    limitations = data["limitations"]
    assert any("individual fish tracking" in lim.lower() for lim in limitations)
    assert data["prediction_type"] == "seasonal_distribution_shift"
