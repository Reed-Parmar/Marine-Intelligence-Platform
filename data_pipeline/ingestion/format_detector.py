"""
Format Detector and Preview Generator for CMLRE Datasets.
Supports TXT (TSV/CSV/whitespace/preambles), CSV, Excel (XLS/XLSX), JSON.
"""

import os
from typing import Any, Dict, List, Optional
import pandas as pd
from .txt_parser import parse_cmlre_txt


def classify_domain(columns: List[str]) -> str:
    """
    Infers the domain_type based on column names in the dataset.
    Supported domain_types: 'edna', 'biodiversity', 'oceanography', 'fisheries', 'otolith', 'cross_domain'
    """
    col_lower = [str(c).lower().replace("_", "").replace(" ", "") for c in columns]
    
    # eDNA indicator keywords
    if any(k in col_lower for k in [
        "targetgene", "dnasequence", "pcrcond", "pcrprimerforward", 
        "sourcematid", "seqmeth", "concentrationunit", "annealingtemp"
    ]):
        return "edna"
    
    # Biodiversity / Species Occurrence indicator keywords
    if any(k in col_lower for k in [
        "scientificname", "occurrenceid", "basisofrecord", "taxonrank", 
        "kingdom", "phylum", "vernacularname", "scientificnameid", "catalogNumber"
    ]):
        return "biodiversity"
    
    # Fisheries indicator keywords
    if any(k in col_lower for k in [
        "catch", "gear", "landing", "trawl", "effort", "cpue", 
        "vesselname", "geartype", "catchweightkg", "efforthours", "fishingzone"
    ]):
        return "fisheries"
        
    # Oceanography indicator keywords
    if any(k in col_lower for k in [
        "salinity", "temperature", "dissolvedoxygen", "ctd", "conductivity", 
        "chlorophyll", "turbidity", "t090c", "sal00", "sbeox0mll", "flecofl"
    ]):
        return "oceanography"
        
    # Otolith indicator keywords
    if any(k in col_lower for k in [
        "otolith", "annuli", "coretoedge", "fishage", "annulicount"
    ]):
        return "otolith"
        
    return "cross_domain"


def detect_format_and_preview(file_path: str) -> Dict[str, Any]:
    """
    Detects the file format, extracts metadata/preamble, reads schema,
    calculates row count and file size, extracts preview, and classifies domain.
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
            "extracted_metadata": {},
            "error": f"File not found: {file_path}"
        }
        
    ext = os.path.splitext(file_path)[1].lower()
    file_size_bytes = os.path.getsize(file_path)
    extracted_metadata: Dict[str, Any] = {}
    
    try:
        if ext in [".txt", ".tsv", ".dat", ".csv", ""]:
            # Use the robust CMLRE text parser
            df_full, extracted_metadata, diagnostics = parse_cmlre_txt(file_path)
            format_name = "txt" if ext != ".csv" else "csv"
        elif ext in [".xls", ".xlsx"]:
            df_full = pd.read_excel(file_path)
            format_name = ext.lstrip(".")
        elif ext == ".json":
            df_full = pd.read_json(file_path)
            format_name = "json"
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        row_count = len(df_full)
        columns = list(df_full.columns)
        
        # Schema definition (column names and dtypes as string)
        schema = {col: str(df_full[col].dtype) for col in columns}
        
        # Domain type classification
        domain_type = classify_domain(columns)
        
        # Data preview (first 5 rows)
        df_preview = df_full.head(5).copy()
        df_preview = df_preview.where(pd.notnull(df_preview), None)
        preview = df_preview.to_dict(orient="records")
        
        return {
            "format": format_name,
            "schema": schema,
            "preview": preview,
            "row_count": row_count,
            "file_size_bytes": file_size_bytes,
            "domain_type": domain_type,
            "columns": columns,
            "extracted_metadata": extracted_metadata,
            "error": None
        }
    except Exception as e:
        return {
            "format": ext.lstrip(".") if ext else "txt",
            "schema": None,
            "preview": None,
            "row_count": 0,
            "file_size_bytes": file_size_bytes,
            "domain_type": "cross_domain",
            "columns": [],
            "extracted_metadata": {},
            "error": str(e)
        }
