"""
Test Unified Marine cross-domain endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.marine_service import MarineService
from backend.app.schemas.marine import MarineObservationItem, MarineSummaryResponse

client = TestClient(app)


def test_marine_summary(monkeypatch):
    """GET /api/v1/marine/summary returns aggregate platform counts."""
    mock_summary = MarineSummaryResponse(
        total_datasets=12,
        oceanography_count=5000,
        fisheries_count=3500,
        biodiversity_count=1200,
        total_species=450
    )
    monkeypatch.setattr(MarineService, "get_marine_summary", lambda: mock_summary)

    response = client.get("/api/v1/marine/summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_datasets"] == 12
    assert data["oceanography_count"] == 5000


def test_marine_observations(monkeypatch):
    """GET /api/v1/marine/observations returns cross-domain items."""
    sample_obs = [
        MarineObservationItem(
            id="obs-1",
            domain="oceanography",
            latitude=9.93,
            longitude=76.26,
            depth=10.0,
            time="2026-03-15T08:00:00Z",
            measurements={"temperature": 28.5, "salinity": 35.2}
        ),
        MarineObservationItem(
            id="obs-2",
            domain="fisheries",
            latitude=9.94,
            longitude=76.27,
            time="2026-03-15T08:30:00Z",
            species_name="Indian Mackerel",
            measurements={"catch_weight_kg": 450.0}
        )
    ]
    monkeypatch.setattr(MarineService, "get_unified_observations", lambda **kwargs: (sample_obs, len(sample_obs)))

    response = client.get("/api/v1/marine/observations")
    assert response.status_code == 200
    res = response.json()
    assert len(res["data"]) == 2
    assert res["data"][0]["domain"] == "oceanography"
    assert res["data"][1]["domain"] == "fisheries"
