import os
import pandas as pd
from typing import Dict, Any, Optional

def classify_domain(columns: list) -> str:
    """
    Infers the domain_type based on column names in the dataset.
    Supported domain_types: 'edna', 'biodiversity', 'oceanography', 'fisheries', 'otolith', 'cross_domain'
    """
    col_lower = [str(c).lower() for c in columns]
    
    # eDNA indicator keywords
    if any(k in col_lower for k in ["target_gene", "dna_sequence", "pcr_cond", "pcr_primer_forward", "source_mat_id", "seq_meth"]):
        return "edna"
    
    # Biodiversity / Species Occurrence indicator keywords
    if any(k in col_lower for k in ["scientificname", "occurrenceid", "basisofrecord", "taxonrank", "kingdom", "phylum", "vernacularname", "scientificnameid"]):
        return "biodiversity"
    
    # Fisheries indicator keywords
    if any(k in col_lower for k in ["catch", "gear", "landing", "trawl", "effort", "cpue", "vessel_name", "gear_type"]):
        return "fisheries"
        
    # Oceanography indicator keywords
    if any(k in col_lower for k in ["salinity", "temperature", "dissolved_oxygen", "ctd", "conductivity", "chlorophyll", "turbidity"]):
        return "oceanography"
        
    # Otolith indicator keywords
    if any(k in col_lower for k in ["otolith", "annuli", "core_to_edge", "fish_age"]):
        return "otolith"
        
    return "cross_domain"


def detect_format_and_preview(file_path: str) -> Dict[str, Any]:
    """
    Detects the file format, reads the schema, calculates row count and file size,
    extracts a preview, and automatically classifies the domain type.
    Supports CSV, TXT (TSV/whitespace), Excel (XLS/XLSX), JSON.
    """
    if not os.path.exists(file_path):
        return {
            "format": None,
            "schema": None,
            "preview": None,
            "row_count": 0,
            "file_size_bytes": 0,
            "domain_type": "cross_domain",
            "columns": [],
            "error": f"File not found: {file_path}"
        }
        
    ext = os.path.splitext(file_path)[1].lower()
    file_size_bytes = os.path.getsize(file_path)
    
    try:
        if ext == '.csv':
            df_full = pd.read_csv(file_path)
            format_name = "csv"
        elif ext == '.txt':
            # Attempt reading as Tab-Separated Values (TSV) first
            try:
                df_full = pd.read_csv(file_path, sep='\t', on_bad_lines='skip')
                if len(df_full.columns) == 1:
                    df_full = pd.read_csv(file_path, sep=r'\s+', on_bad_lines='skip')
            except Exception:
                df_full = pd.read_csv(file_path, sep=r'\s+', on_bad_lines='skip')
            format_name = "txt"
        elif ext in ['.xls', '.xlsx']:
            df_full = pd.read_excel(file_path)
            format_name = ext.lstrip('.')
        elif ext == '.json':
            df_full = pd.read_json(file_path)
            format_name = "json"
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        row_count = len(df_full)
        columns = list(df_full.columns)
        
        # Schema definition (column names and their pandas dtypes as string)
        schema = {col: str(df_full[col].dtype) for col in columns}
        
        # Domain type classification
        domain_type = classify_domain(columns)
        
        # Data preview (first 5 rows) as records (list of dicts) with NaNs replaced by None
        df_preview = df_full.head(5).copy()
        df_preview = df_preview.where(pd.notnull(df_preview), None)
        preview = df_preview.to_dict(orient='records')
        
        return {
            "format": format_name,
            "schema": schema,
            "preview": preview,
            "row_count": row_count,
            "file_size_bytes": file_size_bytes,
            "domain_type": domain_type,
            "columns": columns,
            "error": None
        }
    except Exception as e:
        return {
            "format": ext.lstrip('.'),
            "schema": None,
            "preview": None,
            "row_count": 0,
            "file_size_bytes": file_size_bytes,
            "domain_type": "cross_domain",
            "columns": [],
            "error": str(e)
        }
