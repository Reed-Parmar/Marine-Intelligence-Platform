import os
import pandas as pd
from ingestion_manager import process_upload
from dotenv import load_dotenv

# Load env variables (assuming we run from inside data_pipeline)
load_dotenv(dotenv_path="../.env")

def test_pipeline():
    # Create a dummy CSV file
    dummy_file = "test_dataset.csv"
    df = pd.DataFrame({
        "time": ["2026-08-20T10:00:00Z", "2026-08-20T11:00:00Z"],
        "latitude": [15.5, 15.6],
        "longitude": [72.1, 72.2],
        "temperature": [28.5, 28.7]
    })
    df.to_csv(dummy_file, index=False)
    
    print("Testing pipeline with dummy CSV...")
    
    result = process_upload(dummy_file, dataset_name="Test Sensor Data")
    print("\nResult:")
    print(result)
    
    # Clean up
    if os.path.exists(dummy_file):
        os.remove(dummy_file)

if __name__ == "__main__":
    test_pipeline()
