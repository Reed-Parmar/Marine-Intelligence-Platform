"""
Test Uploads endpoints: staging, preview, processing, duplicate prevention.
"""

import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.dataset_service import DatasetService
from backend.app.services.upload_service import UploadService
from backend.app.schemas.dataset import DatasetResponse

client = TestClient(app)


def test_upload_and_preview_flow(monkeypatch):
    """Tests file upload, format detection, preview generation, and processing."""
    # Mock dataset creation so database connection is not required
    captured_writes = []
    sample_dataset = DatasetResponse(
        id="79e978fe-54ad-4381-9192-3f3667eff991",
        name="Test Staged Dataset",
        domain_type="oceanography",
        status="uploaded"
    )
    monkeypatch.setattr(DatasetService, "create_dataset", lambda req, user_id=None: sample_dataset)
    monkeypatch.setattr(DatasetService, "update_dataset", lambda id, req: sample_dataset)
    monkeypatch.setattr(
        "backend.app.db.database.execute_write",
        lambda query, params=None: captured_writes.append(params or {})
    )

    csv_content = (
        "timestamp,latitude,longitude,station_id,depth,temperature,salinity\n"
        "2026-03-15T08:00:00Z,9.93,76.26,,10.0,28.5,35.2\n"
        "2026-03-15T08:30:00Z,9.94,76.27,   ,20.0,28.2,35.3\n"
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
    assert p_data["dataset_id"] == "79e978fe-54ad-4381-9192-3f3667eff991"
    assert len(captured_writes) == 1
    assert captured_writes[0]["r0_station_id"] is None
    assert captured_writes[0]["r1_station_id"] is None
    assert captured_writes[0]["r0_dataset_id"] == "79e978fe-54ad-4381-9192-3f3667eff991"
    assert captured_writes[0]["r1_dataset_id"] == "79e978fe-54ad-4381-9192-3f3667eff991"

    # 5. Prevent duplicate processing
    dup_resp = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"dataset_name": "Test Staged Dataset", "domain_type": "oceanography"}
    )
    assert dup_resp.status_code == 400
    assert dup_resp.json()["error"]["code"] == "ALREADY_PROCESSED"


def test_oceanography_ingestion_preserves_valid_station_uuid(monkeypatch):
    """A valid station UUID must be passed through unchanged."""
    captured_writes = []
    station_id = "2d8e5d11-6f42-4df4-92cc-5c0e28c1d333"
    dataset_id = "79e978fe-54ad-4381-9192-3f3667eff991"
    monkeypatch.setattr(
        "backend.app.db.database.execute_write",
        lambda query, params=None: captured_writes.append(params or {})
    )

    inserted, skipped = UploadService._ingest_records_into_domain_tables(
        dataset_id=dataset_id,
        domain_type="oceanography",
        records=[
            {
                "timestamp": "2018-05-03",
                "latitude": "10.86",
                "longitude": "72.18",
                "station_id": station_id,
            }
        ],
    )

    assert inserted == 1
    assert skipped == 0
    assert captured_writes[0]["r0_station_id"] == station_id
    assert captured_writes[0]["r0_dataset_id"] == dataset_id


def test_molecular_edna_upload_and_ingestion(monkeypatch):
    """Tests file upload and processing for molecular_edna domain."""
    sample_dataset = DatasetResponse(
        id="c1a2b3c4-54ad-4381-9192-3f3667eff991",
        name="Test eDNA Dataset",
        domain_type="molecular_edna",
        status="uploaded"
    )
    monkeypatch.setattr(DatasetService, "create_dataset", lambda req, user_id=None: sample_dataset)
    monkeypatch.setattr(DatasetService, "update_dataset", lambda id, req: sample_dataset)
    
    captured_writes = []
    def mock_write(query, params=None):
        captured_writes.append(params or {})
        if "edna_samples" in query:
            return {"id": "s1a2b3c4-54ad-4381-9192-3f3667eff991"}
        return None

    monkeypatch.setattr("backend.app.db.database.execute_write", mock_write)

    edna_content = (
        "id\tsamp_name\ttarget_gene\tseq_meth\tread_count\n"
        "NBFGR_01\tMU01\t16S rRNA\tIllumina\t1500\n"
        "NBFGR_02\tMU02\tCOI\tIllumina\t2300\n"
    )
    file_bytes = io.BytesIO(edna_content.encode("utf-8"))

    # 1. Upload
    response = client.post(
        "/api/v1/uploads",
        files={"file": ("dnaderiveddata1.txt", file_bytes, "text/plain")}
    )
    assert response.status_code == 201
    upload_id = response.json()["data"]["upload_id"]

    # 2. Process with domain_type = molecular_edna
    process_resp = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"dataset_name": "Test eDNA Dataset", "domain_type": "molecular_edna"}
    )
    assert process_resp.status_code == 200
    p_data = process_resp.json()["data"]
    assert p_data["status"] == "finalized"
    assert p_data["records_processed"] == 2
    assert p_data["dataset_id"] == "c1a2b3c4-54ad-4381-9192-3f3667eff991"
