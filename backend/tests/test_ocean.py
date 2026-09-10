"""
Test Oceanography endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ocean_service import OceanService
from backend.app.schemas.ocean import OceanObservationResponse, OceanSummaryResponse, OceanTrendItem, OceanTrendResponse

client = TestClient(app)


def test_ocean_observations(monkeypatch):
    """GET /api/v1/ocean/observations returns ocean records."""
    sample = OceanObservationResponse(
        id="ocean-obs-1",
        latitude=9.93,
        longitude=76.26,
        depth=10.0,
        temperature=28.5,
        salinity=35.2,
        dissolved_oxygen=5.8
    )
    monkeypatch.setattr(OceanService, "list_observations", lambda **kwargs: ([sample], 1))

    response = client.get("/api/v1/ocean/observations")
    assert response.status_code == 200
    res = response.json()
    assert len(res["data"]) == 1
    assert res["data"][0]["temperature"] == 28.5


def test_ocean_summary(monkeypatch):
    """GET /api/v1/ocean/summary returns min/max/avg stats."""
    mock_summary = OceanSummaryResponse(
        total_observations=150,
        min_temperature=24.0,
        max_temperature=30.5,
        avg_temperature=28.2,
        min_salinity=34.0,
        max_salinity=36.2,
        avg_salinity=35.4
    )
    monkeypatch.setattr(OceanService, "get_ocean_summary", lambda **kwargs: mock_summary)

    response = client.get("/api/v1/ocean/summary")
    assert response.status_code == 200
    assert response.json()["data"]["avg_temperature"] == 28.2


def test_ocean_trends(monkeypatch):
    """GET /api/v1/ocean/trends returns time series items."""
    mock_trends = OceanTrendResponse(
        variable="temperature",
        trends=[
            OceanTrendItem(time_bucket="2026-01-01", observation_count=50, avg_temperature=27.5),
            OceanTrendItem(time_bucket="2026-02-01", observation_count=60, avg_temperature=28.1),
        ]
    )
    monkeypatch.setattr(OceanService, "get_ocean_trends", lambda **kwargs: mock_trends)

    response = client.get("/api/v1/ocean/trends?variable=temperature")
    assert response.status_code == 200
    res = response.json()["data"]
    assert res["variable"] == "temperature"
    assert len(res["trends"]) == 2
