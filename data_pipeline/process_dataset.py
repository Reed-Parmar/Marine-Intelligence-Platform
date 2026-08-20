import os
import glob
from data_pipeline.ingestion_manager import process_upload
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

dataset_dir = "dataset"
files = glob.glob(os.path.join(dataset_dir, "*.*"))

if files:
    # Test only the first file
    file_path = files[0]
    filename = os.path.basename(file_path)
    print(f"\n--- Processing {filename} ---")
    result = process_upload(file_path, dataset_name=f"Batch: {filename}")
    
    if result["status"] == "success":
        print(f"✅ Success! DB Record ID: {result['dataset_record'].get('id', 'N/A')}")
    else:
        print(f"❌ Failed: {result['message']}")
