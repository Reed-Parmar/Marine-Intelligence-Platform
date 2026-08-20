"""
Test Uploads endpoints: staging, preview, processing, duplicate prevention.
"""

import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.dataset_service import DatasetService
from backend.app.schemas.dataset import DatasetResponse

client = TestClient(app)


def test_upload_and_preview_flow(monkeypatch):
    """Tests file upload, format detection, preview generation, and processing."""
    # Mock dataset creation so database connection is not required
    sample_dataset = DatasetResponse(
        id="d1a2b3c4-test",
        name="Test Staged Dataset",
        domain_type="oceanography",
        status="uploaded"
    )
    monkeypatch.setattr(DatasetService, "create_dataset", lambda req, user_id=None: sample_dataset)
    monkeypatch.setattr(DatasetService, "update_dataset", lambda id, req: sample_dataset)

    csv_content = (
        "time,latitude,longitude,depth,temperature,salinity\n"
        "2026-03-15T08:00:00Z,9.93,76.26,10.0,28.5,35.2\n"
        "2026-03-15T08:30:00Z,9.94,76.27,20.0,28.2,35.3\n"
    )
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))

    # 1. Upload
    response = client.post(
        "/api/v1/uploads",
        files={"file": ("sample_ctd.csv", file_bytes, "text/csv")}
    )
    assert response.status_code == 201
    data = response.json()["data"]
    upload_id = data["upload_id"]
    assert data["detected_format"] == "csv"
    assert data["status"] == "uploaded"

    # 2. Get status
    status_resp = client.get(f"/api/v1/uploads/{upload_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["upload_id"] == upload_id

    # 3. Preview
    preview_resp = client.get(f"/api/v1/uploads/{upload_id}/preview")
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()["data"]
    assert "latitude" in preview_data["headers"]
    assert preview_data["total_preview_rows"] == 2

    # 4. Process upload
    process_resp = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"dataset_name": "Test Staged Dataset", "domain_type": "oceanography"}
    )
    assert process_resp.status_code == 200
    p_data = process_resp.json()["data"]
    assert p_data["status"] == "finalized"
    assert p_data["records_processed"] == 2

    # 5. Prevent duplicate processing
    dup_resp = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"dataset_name": "Test Staged Dataset", "domain_type": "oceanography"}
    )
    assert dup_resp.status_code == 400
    assert dup_resp.json()["error"]["code"] == "ALREADY_PROCESSED"
