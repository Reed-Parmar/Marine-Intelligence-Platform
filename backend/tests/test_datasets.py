"""
Test Datasets endpoints: authentication, authorization, list, create, get, quality, provenance.
"""

from fastapi.testclient import TestClient
from backend.app.auth.supabase_auth import get_current_user
from backend.app.main import app
from backend.app.schemas.auth import UserProfile, UserRole
from backend.app.schemas.dataset import DatasetResponse
from backend.app.services.dataset_service import DatasetService

client = TestClient(app)


def test_list_datasets_public():
    """Request to GET /api/v1/datasets returns 200 catalog."""
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    assert "data" in response.json()


def test_list_datasets_authenticated(monkeypatch):
    """Authenticated user can list datasets."""
    mock_user = UserProfile(id="user-1", email="user@cmlre.gov.in", role=UserRole.USER)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    sample_dataset = DatasetResponse(
        id="d1a2b3c4-test",
        name="Arabian Sea CTD Survey 2026",
        domain_type="oceanography",
        status="standardized",
        quality_status="passed",
        quality_score=98.5
    )
    monkeypatch.setattr(DatasetService, "list_datasets", lambda **kwargs: ([sample_dataset], 1))

    try:
        response = client.get("/api/v1/datasets")
        assert response.status_code == 200
        res = response.json()
        assert "data" in res
        assert len(res["data"]) == 1
        assert res["data"][0]["name"] == "Arabian Sea CTD Survey 2026"
    finally:
        app.dependency_overrides.clear()


def test_get_dataset_by_id(monkeypatch):
    """Authenticated user can get dataset metadata."""
    mock_user = UserProfile(id="user-1", email="user@cmlre.gov.in", role=UserRole.USER)
    app.dependency_overrides[get_current_user] = lambda: mock_user

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

    try:
        response = client.get("/api/v1/datasets/d1a2b3c4-test")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == "d1a2b3c4-test"

        not_found_res = client.get("/api/v1/datasets/non-existent-id")
        assert not_found_res.status_code == 404
        assert not_found_res.json()["error"]["code"] == "DATASET_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_update_dataset_forbidden_for_non_owner(monkeypatch):
    """User cannot modify another user's dataset unless admin."""
    regular_user = UserProfile(id="user-2", email="user2@cmlre.gov.in", role=UserRole.USER)
    app.dependency_overrides[get_current_user] = lambda: regular_user

    sample_dataset = DatasetResponse(
        id="d1a2b3c4-test",
        name="Arabian Sea CTD Survey 2026",
        domain_type="oceanography",
        uploaded_by="user-1"  # Owned by user-1
    )
    monkeypatch.setattr(DatasetService, "get_dataset_by_id", lambda id: sample_dataset)

    try:
        response = client.patch(
            "/api/v1/datasets/d1a2b3c4-test",
            json={"name": "New Dataset Name"}
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"
    finally:
        app.dependency_overrides.clear()


def test_get_dataset_quality_and_provenance(monkeypatch):
    """GET quality and provenance endpoints."""
    mock_user = UserProfile(id="user-1", email="user@cmlre.gov.in", role=UserRole.USER)
    app.dependency_overrides[get_current_user] = lambda: mock_user

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

    try:
        q_resp = client.get("/api/v1/datasets/d1a2b3c4-test/quality")
        assert q_resp.status_code == 200
        assert q_resp.json()["data"]["quality_score"] == 98.5

        p_resp = client.get("/api/v1/datasets/d1a2b3c4-test/provenance")
        assert p_resp.status_code == 200
        assert "provenance_metadata" in p_resp.json()["data"]
    finally:
        app.dependency_overrides.clear()
