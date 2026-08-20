import os
import sys
import glob
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

# Add project root to sys.path to allow imports
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from data_pipeline.ingestion_manager import process_upload

def process_all_datasets(dataset_dir: str = None):
    """
    Scans the dataset directory and processes every file through the ingestion pipeline.
    """
    if dataset_dir is None:
        dataset_dir = str(root_dir / "dataset")
        
    print("=" * 78)
    print("  CMLRE MARINE INTELLIGENCE PLATFORM - DATA INGESTION ENGINE")
    print("=" * 78)
    print(f"Dataset Directory: {dataset_dir}")
    
    files = sorted(glob.glob(os.path.join(dataset_dir, "*.*")))
    if not files:
        print(f"[WARN] No dataset files found in {dataset_dir}")
        return []
        
    print(f"Found {len(files)} dataset files to process:\n")
    for idx, f in enumerate(files, 1):
        print(f"  {idx}. {os.path.basename(f)} ({os.path.getsize(f):,} bytes)")
        
    results = []
    
    for file_path in files:
        filename = os.path.basename(file_path)
        dataset_name = f"CMLRE: {filename}"
        
        result = process_upload(file_path, dataset_name=dataset_name)
        results.append(result)
        
        if result["status"] == "success":
            print(f"  [SUCCESS] {filename}")
            print(f"     * Dataset ID:   {result['dataset_id']}")
            print(f"     * Domain:       {result['domain_type']}")
            print(f"     * Total Rows:   {result['row_count']:,}")
            print(f"     * Total Cols:   {result['columns_count']}")
            print(f"     * Storage Path: {result['storage_path']}")
        else:
            print(f"  [FAILED] {filename}: {result['message']}")
            
    print("\n" + "=" * 78)
    print("  INGESTION SUMMARY")
    print("=" * 78)
    print(f"{'Filename':<22} | {'Domain':<13} | {'Rows':<8} | {'Cols':<5} | {'Status':<10} | {'Dataset ID'}")
    print("-" * 78)
    for r in results:
        fname = os.path.basename(r.get("storage_path", "unknown")).split("/")[-1] if r.get("storage_path") else r.get("name", "unknown")
        status_str = "SUCCESS" if r["status"] == "success" else "FAILED"
        domain = r.get("domain_type", "N/A")
        rows = f"{r.get('row_count', 0):,}" if r.get("row_count") is not None else "N/A"
        cols = str(r.get("columns_count", "N/A"))
        ds_id = r.get("dataset_id", "N/A")
        print(f"{fname:<22} | {domain:<13} | {rows:<8} | {cols:<5} | {status_str:<10} | {ds_id}")
        
    print("=" * 78)
    return results

if __name__ == "__main__":
    process_all_datasets()
