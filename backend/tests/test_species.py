"""
Test Species and Occurrence endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.species_service import SpeciesService
from backend.app.schemas.species import SpeciesDistributionResponse, SpeciesOccurrenceResponse, SpeciesResponse

client = TestClient(app)


def test_list_species(monkeypatch):
    """GET /api/v1/species returns taxonomy catalog items."""
    sample_sp = SpeciesResponse(
        id="sp-1",
        scientific_name="Rastrelliger kanagurta",
        common_name="Indian Mackerel",
        kingdom="Animalia",
        phylum="Chordata",
        class_name="Actinopterygii",
        order="Scombriformes",
        family="Scombridae",
        genus="Rastrelliger"
    )
    monkeypatch.setattr(SpeciesService, "search_species", lambda **kwargs: ([sample_sp], 1))

    response = client.get("/api/v1/species?search=mackerel")
    assert response.status_code == 200
    res = response.json()
    assert len(res["data"]) == 1
    assert res["data"][0]["scientific_name"] == "Rastrelliger kanagurta"
    assert res["data"][0]["class"] == "Actinopterygii"


def test_get_species_by_id(monkeypatch):
    """GET /api/v1/species/{id} returns details."""
    sample_sp = SpeciesResponse(
        id="sp-1",
        scientific_name="Rastrelliger kanagurta",
        common_name="Indian Mackerel"
    )
    monkeypatch.setattr(SpeciesService, "get_species_by_id", lambda id: sample_sp if id == "sp-1" else None)

    response = client.get("/api/v1/species/sp-1")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == "sp-1"

    err_response = client.get("/api/v1/species/invalid-id")
    assert err_response.status_code == 404
    assert err_response.json()["error"]["code"] == "SPECIES_NOT_FOUND"


def test_get_species_occurrences_and_distribution(monkeypatch):
    """GET occurrences and distribution endpoints."""
    occ = SpeciesOccurrenceResponse(
        id="occ-1",
        species_id="sp-1",
        scientific_name="Rastrelliger kanagurta",
        latitude=9.93,
        longitude=76.26,
        depth=15.0
    )
    dist = SpeciesDistributionResponse(
        species_id="sp-1",
        occurrence_count=45,
        min_latitude=8.0,
        max_latitude=15.0,
        min_longitude=72.0,
        max_longitude=78.0
    )
    monkeypatch.setattr(SpeciesService, "get_species_occurrences", lambda **kwargs: ([occ], 1))
    monkeypatch.setattr(SpeciesService, "get_species_distribution", lambda id: dist if id == "sp-1" else None)

    occ_res = client.get("/api/v1/species/sp-1/occurrences")
    assert occ_res.status_code == 200
    assert len(occ_res.json()["data"]) == 1

    dist_res = client.get("/api/v1/species/sp-1/distribution")
    assert dist_res.status_code == 200
    assert dist_res.json()["data"]["occurrence_count"] == 45
