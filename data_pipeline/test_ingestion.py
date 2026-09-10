import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Find root .env file
root_dir = Path(__file__).resolve().parent.parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

# Add project root to sys.path
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from data_pipeline.ingestion.format_detector import detect_format_and_preview, classify_domain
from data_pipeline.ingestion.ingestion_manager import process_upload
from data_pipeline.storage.file_handler import get_supabase_client

def test_domain_classification():
    print("[Test 1/4] Testing domain classification heuristics...")
    assert classify_domain(["target_gene", "DNA_sequence", "pcr_cond"]) == "edna"
    assert classify_domain(["scientificName", "occurrenceID", "decimalLatitude"]) == "biodiversity"
    assert classify_domain(["trawl_catch", "gear_type", "landing_weight"]) == "fisheries"
    assert classify_domain(["temperature", "salinity", "dissolved_oxygen"]) == "oceanography"
    assert classify_domain(["otolith_image", "annuli_count", "fish_age"]) == "otolith"
    print("  [PASS] Domain classification logic verified.")

def test_format_detector_on_real_datasets():
    print("\n[Test 2/4] Testing format detector on real datasets in dataset/ ...")
    dataset_dir = root_dir / "dataset"
    expected_files = ["dnaderiveddata1.txt", "occurrence.txt", "occurrence1.txt", "occurrence2.txt", "occurrence3.txt"]
    
    for filename in expected_files:
        filepath = str(dataset_dir / filename)
        if not os.path.exists(filepath):
            print(f"  [WARN] File {filename} not found, skipping.")
            continue
            
        res = detect_format_and_preview(filepath)
        assert res["error"] is None, f"Detection failed for {filename}: {res['error']}"
        assert res["row_count"] > 0, f"Expected > 0 rows in {filename}"
        assert len(res["columns"]) > 0, f"Expected columns in {filename}"
        assert res["domain_type"] in ["edna", "biodiversity"], f"Unexpected domain for {filename}: {res['domain_type']}"
        print(f"  [PASS] {filename:<20}: {res['domain_type']:<13} ({res['row_count']:,} rows, {len(res['columns'])} cols)")

def test_pipeline_with_dummy_csv():
    print("\n[Test 3/4] Testing end-to-end pipeline with synthetic oceanographic CSV...")
    dummy_file = str(root_dir / "data_pipeline" / "test_temp_ocean_data.csv")
    df = pd.DataFrame({
        "timestamp": ["2026-08-20T10:00:00Z", "2026-08-20T11:00:00Z"],
        "decimalLatitude": [15.5, 15.6],
        "decimalLongitude": [72.1, 72.2],
        "temperature": [28.5, 28.7],
        "salinity": [35.2, 35.4]
    })
    df.to_csv(dummy_file, index=False)
    
    result = None
    try:
        result = process_upload(dummy_file, dataset_name="Synthetic Oceanographic Test")
        assert result["status"] == "success", f"Pipeline failed: {result.get('message')}"
        assert result["domain_type"] == "oceanography"
        assert result["row_count"] == 2
        print(f"  [PASS] Synthetic pipeline run succeeded. Dataset ID: {result['dataset_id']}")
    finally:
        # Cleanup temporary file
        if os.path.exists(dummy_file):
            os.remove(dummy_file)
            
        # Cleanup test DB record if created
        if result and result.get("dataset_id"):
            try:
                supabase = get_supabase_client()
                supabase.table("datasets").delete().eq("id", result["dataset_id"]).execute()
                print("  [CLEANUP] Removed synthetic test database record.")
            except Exception as e:
                print("  [WARN] DB cleanup failed:", e)

def test_pipeline_with_first_real_dataset():
    print("\n[Test 4/4] Testing end-to-end pipeline with dataset/dnaderiveddata1.txt ...")
    real_file = str(root_dir / "dataset" / "dnaderiveddata1.txt")
    if not os.path.exists(real_file):
        print("  [WARN] dnaderiveddata1.txt not found, skipping.")
        return
        
    result = process_upload(real_file, dataset_name="Test eDNA Sequences")
    assert result["status"] == "success", f"Pipeline failed on real dataset: {result.get('message')}"
    assert result["domain_type"] == "edna"
    print(f"  [PASS] eDNA real dataset ingestion succeeded! Dataset ID: {result['dataset_id']}")

if __name__ == "__main__":
    print("=" * 65)
    print("  RUNNING DATA PIPELINE INTEGRATION TEST SUITE")
    print("=" * 65)
    test_domain_classification()
    test_format_detector_on_real_datasets()
    test_pipeline_with_dummy_csv()
    test_pipeline_with_first_real_dataset()
    print("\n" + "=" * 65)
    print("  ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 65)
