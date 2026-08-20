import os
from .format_detector import detect_format_and_preview
from .file_handler import upload_to_storage
from .dataset_registrar import register_dataset

def process_upload(file_path: str, dataset_name: str, project_id: str = None) -> dict:
    """
    Main orchestration function for the Data Ingestion Engine.
    1. Detects format and reads schema.
    2. Uploads the file to Supabase Storage.
    3. Registers the dataset metadata in Supabase PostgreSQL.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}
    
    print(f"Starting processing for: {file_path}")
    
    # 1. Format detection and preview
    detection_result = detect_format_and_preview(file_path)
    if detection_result.get("error"):
        return {"status": "error", "message": f"Format detection failed: {detection_result['error']}"}
        
    print(f"Format detected: {detection_result['format']}")
    
    # 2. Upload to Storage
    try:
        storage_path = upload_to_storage(file_path)
        print(f"File uploaded successfully to: {storage_path}")
    except Exception as e:
        return {"status": "error", "message": f"Storage upload failed: {str(e)}"}
        
    # 3. Register Dataset
    try:
        record = register_dataset(
            name=dataset_name,
            storage_path=storage_path,
            schema=detection_result["schema"],
            format_type=detection_result["format"],
            project_id=project_id,
            status="processed"
        )
        print("Dataset registered successfully.")
    except Exception as e:
        return {"status": "error", "message": f"Database registration failed: {str(e)}"}
        
    return {
        "status": "success",
        "dataset_record": record,
        "preview": detection_result["preview"]
    }
