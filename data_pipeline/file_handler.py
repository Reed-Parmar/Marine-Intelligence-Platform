import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    return create_client(url, key)

def upload_to_storage(file_path: str, bucket_name: str = "marine-files") -> str:
    """
    Uploads a local file to a Supabase Storage bucket.
    Returns the storage path upon success.
    """
    supabase = get_supabase_client()
    
    # Ensure bucket exists (this uses the service role key ideally)
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        if bucket_name not in bucket_names:
            supabase.storage.create_bucket(bucket_name)
    except Exception as e:
        # Ignore bucket creation errors (might lack permissions with anon key)
        print(f"Warning checking/creating bucket: {e}")

    file_name = os.path.basename(file_path)
    storage_path = f"uploads/{file_name}"
    
    with open(file_path, "rb") as f:
        # Check if file exists, optionally remove or just upsert
        res = supabase.storage.from_(bucket_name).upload(
            file=f,
            path=storage_path,
            file_options={"cache-control": "3600", "upsert": "true"}
        )
    
    return storage_path
