import os
import pandas as pd
import json

def detect_format_and_preview(file_path: str):
    """
    Detects the file format, reads the schema, and extracts a small preview.
    Supports CSV, TXT, Excel, JSON.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.csv':
            df = pd.read_csv(file_path, nrows=5)
        elif ext == '.txt':
            # Assuming tab separated or space separated for TXT files for oceanographic data
            df = pd.read_csv(file_path, sep='\t', nrows=5)
            if len(df.columns) == 1:
                df = pd.read_csv(file_path, sep=r'\s+', nrows=5)
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, nrows=5)
        elif ext == '.json':
            df = pd.read_json(file_path)
            df = df.head(5)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Schema definition (column names and their pandas dtypes as string)
        schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        # Data preview as records (list of dicts)
        # Using json to handle NaNs appropriately (filling with None)
        df_clean = df.where(pd.notnull(df), None)
        preview = df_clean.to_dict(orient='records')
        
        return {
            "format": ext.strip('.'),
            "schema": schema,
            "preview": preview,
            "error": None
        }
    except Exception as e:
        return {
            "format": ext.strip('.'),
            "schema": None,
            "preview": None,
            "error": str(e)
        }
