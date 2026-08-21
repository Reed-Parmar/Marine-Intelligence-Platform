"""
Batch Ingestion & Quality Processing Runner for CMLRE Datasets.
Scans and processes all files in dataset/, performing parsing, schema normalization,
Phase 4 Quality Control & Scientific Standardisation, canonical CSV/XLSX export,
Supabase storage upload, and dataset registration in PostgreSQL.
"""

import glob
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Find root .env file
root_dir = Path(__file__).resolve().parent.parent.parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

# Add project root to sys.path to allow imports
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from data_pipeline.ingestion.ingestion_manager import process_upload


def process_all_datasets(dataset_dir: str = None):
    """
    Scans the dataset directory and processes every file through the complete
    Phase 3 Ingestion + Phase 4 Quality Control pipeline.
    """
    if dataset_dir is None:
        dataset_dir = str(root_dir / "dataset")
        
    print("=" * 96)
    print("  CMLRE MARINE INTELLIGENCE PLATFORM - END-TO-END INGESTION & QUALITY PIPELINE")
    print("=" * 96)
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
        
        result = process_upload(
            file_path, 
            dataset_name=dataset_name,
            export_canonical=True,
            export_xlsx=True
        )
        results.append(result)
        
        if result["status"] == "success":
            qc_score_str = f"{result.get('quality_score', 'N/A')}/100" if result.get('quality_score') is not None else "Pending"
            qc_status_str = result.get('quality_status', 'pending').upper()
            print(f"  [SUCCESS] {filename}")
            print(f"     * Dataset ID:    {result['dataset_id']}")
            print(f"     * Domain:        {result['domain_type']}")
            print(f"     * Total Rows:    {result['row_count']:,}")
            print(f"     * Total Cols:    {result['columns_count']}")
            print(f"     * QC Score:      {qc_score_str} ({qc_status_str})")
            print(f"     * Storage Path:  {result['storage_path']}")
            print(f"     * Canonical CSV: {result.get('canonical_csv_path')}")
            print(f"     * Canonical XLSX:{result.get('canonical_xlsx_path')}")
        else:
            print(f"  [FAILED] {filename}: {result['message']}")
            
    print("\n" + "=" * 96)
    print("  END-TO-END PIPELINE SUMMARY (PHASE 3 INGESTION + PHASE 4 QUALITY CONTROL)")
    print("=" * 96)
    print(f"{'Filename':<22} | {'Domain':<13} | {'Rows':<7} | {'Cols':<5} | {'QC Score':<9} | {'QC Status':<9} | {'Ingest Status'}")
    print("-" * 96)
    for r in results:
        fname = os.path.basename(r.get("storage_path", "unknown")).split("/")[-1] if r.get("storage_path") else r.get("name", "unknown")
        status_str = "SUCCESS" if r["status"] == "success" else "FAILED"
        domain = r.get("domain_type", "N/A")
        rows = f"{r.get('row_count', 0):,}" if r.get("row_count") is not None else "N/A"
        cols = str(r.get("columns_count", "N/A"))
        qc_score = f"{r.get('quality_score'):.1f}" if r.get("quality_score") is not None else "N/A"
        qc_status = r.get("quality_status", "N/A").upper()
        print(f"{fname:<22} | {domain:<13} | {rows:<7} | {cols:<5} | {qc_score:<9} | {qc_status:<9} | {status_str}")
        
    print("=" * 96)
    return results


if __name__ == "__main__":
    process_all_datasets()
