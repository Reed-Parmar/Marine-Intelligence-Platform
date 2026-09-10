"""
Canonical Dataset Exporter.
Generates clean Canonical CSV and multi-sheet XLSX workbooks with character sanitization.
"""

import os
import re
from typing import Any, Dict, Optional
import pandas as pd

# Openpyxl illegal characters regex (non-printable control chars)
ILLEGAL_XLSX_CHARS = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]")


def sanitize_for_excel(val: Any) -> Any:
    """Removes non-printable control characters that are invalid in Excel XML."""
    if isinstance(val, str):
        return ILLEGAL_XLSX_CHARS.sub("", val)
    return val


def export_canonical_csv(df: pd.DataFrame, output_path: str) -> str:
    """
    Exports clean canonical CSV with single header row, UTF-8 encoding,
    and standard missing value formatting.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def export_canonical_xlsx(
    df: pd.DataFrame, 
    output_path: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Exports canonical multi-sheet Excel (.xlsx) workbook:
    - Sheet 1: 'Data' containing the canonical tabular dataset.
    - Sheet 2: 'Metadata' containing extracted preamble & provenance key-values.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Sanitize dataframe values for Excel XML safety
    clean_df = df.map(sanitize_for_excel)
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        clean_df.to_excel(writer, sheet_name="Data", index=False)
        
        # Prepare metadata dataframe
        if metadata:
            meta_records = [
                {"Key": str(k), "Value": sanitize_for_excel(str(v))} 
                for k, v in metadata.items()
            ]
            meta_df = pd.DataFrame(meta_records)
        else:
            meta_df = pd.DataFrame([{"Key": "Status", "Value": "Standardized"}])
            
        meta_df.to_excel(writer, sheet_name="Metadata", index=False)
        
    return output_path
