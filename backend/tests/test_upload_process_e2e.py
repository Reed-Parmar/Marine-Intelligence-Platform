import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_occurrence_upload_and_process():
    content = (
        "id\tscientificName\tdecimalLatitude\tdecimalLongitude\tminimumDepthInMeters\tindividualCount\teventDate\tbasisOfRecord\toccurrenceStatus\n"
        "93630\tAsterionella japonica\t16.2551\t69.9113\t25\t1\t2009-02-16/2009-02-23\tHumanObservation\tpresent\n"
        "93631\tBacteriastrum hyalinum\t16.2551\t69.9113\t25\t1\t2009-02-16/2009-02-23\tHumanObservation\tpresent\n"
        "93632\tChaetoceros concavicornis\t16.2551\t69.9113\t25\t1\t2009-02-16/2009-02-23\tHumanObservation\tpresent\n"
    )
    
    files = {"file": ("occurrence.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    res = client.post("/api/v1/uploads", files=files)
    assert res.status_code == 201
    upload_id = res.json()["data"]["upload_id"]

    prev_res = client.get(f"/api/v1/uploads/{upload_id}/preview")
    assert prev_res.status_code == 200
    assert len(prev_res.json()["data"]["sample_rows"]) == 3

    proc_res = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"domain_type": "biodiversity", "dataset_name": "occurrence_automated_test"}
    )
    assert proc_res.status_code == 200
    proc_data = proc_res.json()["data"]
    assert proc_data["status"] == "finalized"
    assert proc_data["records_processed"] == 3


def test_edna_upload_and_process():
    content = (
        "sample_code\tlatitude\tlongitude\tdepth_meters\ttarget_gene\tsequencing_platform\tassigned_scientific_name\tread_count\tblast_identity_percentage\n"
        "EDNA-AS-01\t10.85\t72.25\t25.0\t16S rRNA / COI\tIllumina NovaSeq 6000\tSynechococcus sp.\t1420\t99.4\n"
        "EDNA-AS-02\t10.85\t72.25\t50.0\t16S rRNA / COI\tIllumina NovaSeq 6000\tPelagibacter ubique\t3850\t98.9\n"
    )

    files = {"file": ("dnaderiveddata1.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    res = client.post("/api/v1/uploads", files=files)
    assert res.status_code == 201
    upload_id = res.json()["data"]["upload_id"]

    prev_res = client.get(f"/api/v1/uploads/{upload_id}/preview")
    assert prev_res.status_code == 200

    proc_res = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"domain_type": "molecular_edna", "dataset_name": "edna_automated_test"}
    )
    assert proc_res.status_code == 200
    proc_data = proc_res.json()["data"]
    assert proc_data["status"] == "finalized"
    assert proc_data["records_processed"] == 2


def test_oceanography_upload_and_process():
    content = (
        "station_id,latitude,longitude,depth_meters,temperature_celsius,salinity_psu,dissolved_oxygen_mgl,chlorophyll_mg_m3,ph,timestamp\n"
        "CMLRE-CTD-01,15.42,72.18,10.0,28.45,35.21,5.82,1.45,8.14,2023-08-15T06:00:00Z\n"
        "CMLRE-CTD-01,15.42,72.18,50.0,26.12,35.88,4.15,0.82,8.05,2023-08-15T06:15:00Z\n"
    )

    files = {"file": ("arabian_sea_ctd.csv", io.BytesIO(content.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/uploads", files=files)
    assert res.status_code == 201
    upload_id = res.json()["data"]["upload_id"]

    proc_res = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"domain_type": "oceanography", "dataset_name": "oceanography_automated_test"}
    )
    assert proc_res.status_code == 200
    proc_data = proc_res.json()["data"]
    assert proc_data["status"] == "finalized"
    assert proc_data["records_processed"] == 2


def test_fisheries_upload_and_process():
    content = (
        "timestamp,latitude,longitude,species_name,catch_weight_kg,fishing_effort_hours,gear_type,fishing_zone,vessel_name\n"
        "2023-04-12T05:30:00Z,10.25,75.80,Rastrelliger kanagurta,450.5,6.5,Gillnet,South-West Coast EEZ,Sagar Kripa\n"
        "2023-04-12T07:15:00Z,10.35,75.90,Sardinella longiceps,720.0,5.0,Purse Seine,South-West Coast EEZ,Sagar Kripa\n"
    )

    files = {"file": ("fisheries_landing.csv", io.BytesIO(content.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/uploads", files=files)
    assert res.status_code == 201
    upload_id = res.json()["data"]["upload_id"]

    proc_res = client.post(
        f"/api/v1/uploads/{upload_id}/process",
        json={"domain_type": "fisheries", "dataset_name": "fisheries_automated_test"}
    )
    assert proc_res.status_code == 200
    proc_data = proc_res.json()["data"]
    assert proc_data["status"] == "finalized"
    assert proc_data["records_processed"] == 2
