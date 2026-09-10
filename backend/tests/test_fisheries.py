"""
Test Fisheries endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.fisheries_service import FisheriesService
from backend.app.schemas.fisheries import FisheriesObservationResponse, FisheriesSummaryResponse, FisheriesTrendItem, FisheriesTrendResponse

client = TestClient(app)


def test_fisheries_observations(monkeypatch):
    """GET /api/v1/fisheries/observations returns catch records."""
    sample = FisheriesObservationResponse(
        id="fish-1",
        scientific_name="Rastrelliger kanagurta",
        common_name="Indian Mackerel",
        latitude=9.93,
        longitude=76.26,
        catch_weight_kg=350.0,
        effort_hours=4.5,
        gear_type="Trawl"
    )
    monkeypatch.setattr(FisheriesService, "list_observations", lambda **kwargs: ([sample], 1))

    response = client.get("/api/v1/fisheries/observations")
    assert response.status_code == 200
    res = response.json()
    assert len(res["data"]) == 1
    assert res["data"][0]["common_name"] == "Indian Mackerel"


def test_fisheries_summary(monkeypatch):
    """GET /api/v1/fisheries/summary returns catch totals."""
    mock_summary = FisheriesSummaryResponse(
        total_records=250,
        total_catch_kg=45000.0,
        avg_catch_kg=180.0,
        total_effort_hours=1200.0,
        distinct_species_count=35,
        distinct_zones_count=6
    )
    monkeypatch.setattr(FisheriesService, "get_fisheries_summary", lambda **kwargs: mock_summary)

    response = client.get("/api/v1/fisheries/summary")
    assert response.status_code == 200
    assert response.json()["data"]["total_catch_kg"] == 45000.0
