"""
Test Datasets endpoints: list, create, get, quality, provenance.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.dataset_service import DatasetService
from backend.app.schemas.dataset import DatasetResponse

client = TestClient(app)


def test_list_datasets(monkeypatch):
    """GET /api/v1/datasets returns list with pagination metadata."""
    sample_dataset = DatasetResponse(
        id="d1a2b3c4-test",
        name="Arabian Sea CTD Survey 2026",
        domain_type="oceanography",
        status="standardized",
        quality_status="passed",
        quality_score=98.5
    )
    monkeypatch.setattr(DatasetService, "list_datasets", lambda **kwargs: ([sample_dataset], 1))

    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    res = response.json()
    assert "data" in res
    assert "meta" in res
    assert len(res["data"]) == 1
    assert res["data"][0]["name"] == "Arabian Sea CTD Survey 2026"
    assert res["meta"]["total"] == 1


def test_get_dataset_by_id(monkeypatch):
    """GET /api/v1/datasets/{id} returns full metadata."""
    sample_dataset = DatasetResponse(
        id="d1a2b3c4-test",
        name="Arabian Sea CTD Survey 2026",
        domain_type="oceanography",
        status="standardized",
        quality_status="passed",
        quality_score=98.5,
        validation_notes="Predefined QC criteria passed."
    )
    monkeypatch.setattr(DatasetService, "get_dataset_by_id", lambda id: sample_dataset if id == "d1a2b3c4-test" else None)

    response = client.get("/api/v1/datasets/d1a2b3c4-test")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == "d1a2b3c4-test"

    # Test 404
    not_found_res = client.get("/api/v1/datasets/non-existent-id")
    assert not_found_res.status_code == 404
    assert not_found_res.json()["error"]["code"] == "DATASET_NOT_FOUND"


def test_get_dataset_quality_and_provenance(monkeypatch):
    """GET quality and provenance endpoints."""
    sample_dataset = DatasetResponse(
        id="d1a2b3c4-test",
        name="Arabian Sea CTD Survey 2026",
        domain_type="oceanography",
        quality_status="passed",
        quality_score=98.5,
        validation_notes="Quality Score: 98.5/100",
        provenance_metadata={"records_count": 100, "sensor": "Seabird SBE 19plus"}
    )
    monkeypatch.setattr(DatasetService, "get_dataset_by_id", lambda id: sample_dataset)

    q_resp = client.get("/api/v1/datasets/d1a2b3c4-test/quality")
    assert q_resp.status_code == 200
    assert q_resp.json()["data"]["quality_score"] == 98.5

    p_resp = client.get("/api/v1/datasets/d1a2b3c4-test/provenance")
    assert p_resp.status_code == 200
    assert "provenance_metadata" in p_resp.json()["data"]
