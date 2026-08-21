"""
Robust CMLRE Text & Delimited Dataset Parser.
Handles multi-encoding, preambles/metadata extraction, automatic delimiter detection,
header row detection, multiline fields, missing value markers, and non-tabular validation.
"""

import csv
import io
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# Standard missing value markers encountered in marine & scientific datasets
MISSING_VALUE_MARKERS = {
    "-999", "-9999", "-999.0", "-9999.0", "9999", "999.0",
    "NA", "N/A", "na", "n/a", "N.A.", "NULL", "null", "None", "none",
    "ND", "nd", "N/D", "n/d", "?", "*", "-", "--", "NaN", "nan"
}

# Comment line prefixes commonly found in scientific preambles
COMMENT_PREFIXES = ("#", "*", "//", "rem", "/*", "%", "!")


def detect_file_encoding(file_path: str) -> str:
    """
    Attempts to detect the file encoding by testing candidate decoders across the file.
    Falls back gracefully across utf-8, utf-8-sig, cp1252, latin-1.
    """
    with open(file_path, "rb") as f:
        raw_bytes = f.read(10 * 1024 * 1024)
        
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw_bytes.startswith(b"\xff\xfe") or raw_bytes.startswith(b"\xfe\xff"):
        return "utf-16"
        
    for enc in ["utf-8", "utf-8-sig", "cp1252", "latin-1", "iso-8859-1"]:
        try:
            raw_bytes.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"



def extract_preamble_metadata(lines: List[str]) -> Tuple[Dict[str, Any], int]:
    """
    Scans initial lines of a text file for metadata, comments, and headers.
    Returns extracted metadata dictionary and the index of the first potential table line.
    """
    metadata: Dict[str, Any] = {}
    preamble_lines: List[str] = []
    first_table_idx = 0

    for idx, line in enumerate(lines):
        trimmed = line.strip()
        if not trimmed:
            continue

        is_comment = any(trimmed.startswith(prefix) for prefix in COMMENT_PREFIXES)
        kv_match = re.match(r"^[\*#\/\s]*([A-Za-z0-9_\s\-\.]{2,40})[:=]\s*(.+)$", trimmed)
        
        if is_comment or (kv_match and not ("\t" in trimmed or "," in trimmed or ";" in trimmed)):
            preamble_lines.append(trimmed)
            if kv_match:
                k = kv_match.group(1).strip().lower().replace(" ", "_")
                v = kv_match.group(2).strip()
                metadata[k] = v
            first_table_idx = idx + 1
        elif trimmed.upper() in ["*END*", "*END", "#END", "#DATA"]:
            first_table_idx = idx + 1
            break
        else:
            first_table_idx = idx
            break

    if preamble_lines:
        metadata["_preamble_raw"] = "\n".join(preamble_lines[:50])

    return metadata, first_table_idx


def is_valid_column_name(col: str) -> bool:
    """Checks if a string is a plausible column header rather than a prose sentence."""
    col = col.strip()
    if not col or len(col) > 60:
        return False
    if col.endswith(".") or col.endswith("?") or col.endswith("!"):
        return False
    # Headers should not contain multiple english words with sentence casing
    if len(col.split()) > 5:
        return False
    return True


def detect_delimiter_and_header(lines: List[str], start_idx: int) -> Tuple[Optional[str], int, List[str]]:
    """
    Analyzes lines starting at start_idx to find the best delimiter and header row.
    Evaluates Tab, Comma, Semicolon, Pipe, and Whitespace.
    """
    candidate_delimiters = ["\t", ",", ";", "|"]
    best_delimiter = None
    best_header_idx = start_idx
    best_score = -1
    best_columns: List[str] = []

    total_lines = len(lines)
    max_scan = min(start_idx + 15, total_lines)

    for line_idx in range(start_idx, max_scan):
        line = lines[line_idx].strip()
        if not line:
            continue

        for delim in candidate_delimiters:
            parts = [p.strip().strip('"\'') for p in line.split(delim)]
            if len(parts) < 2:
                continue

            if not all(is_valid_column_name(p) for p in parts if p):
                continue

            non_numeric = sum(1 for p in parts if p and not re.match(r"^-?\d+(\.\d+)?$", p))
            header_ratio = non_numeric / len(parts) if parts else 0

            sample_data_lines = [l.strip() for l in lines[line_idx + 1: line_idx + 10] if l.strip()]
            consistent_rows = 0
            for dl in sample_data_lines:
                dl_parts = dl.split(delim)
                if abs(len(dl_parts) - len(parts)) <= 1:
                    consistent_rows += 1

            score = (len(parts) * 10) + (header_ratio * 20) + (consistent_rows * 5)

            if score > best_score and len(parts) >= 2 and header_ratio >= 0.5:
                best_score = score
                best_delimiter = delim
                best_header_idx = line_idx
                best_columns = parts

    # Fallback to whitespace only for structured data tables
    if best_delimiter is None:
        for line_idx in range(start_idx, max_scan):
            line = lines[line_idx].strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split()]
            if len(parts) >= 2 and all(is_valid_column_name(p) for p in parts):
                non_numeric = sum(1 for p in parts if p and not re.match(r"^-?\d+(\.\d+)?$", p))
                if non_numeric / len(parts) >= 0.7:
                    sample_data_lines = [l.strip() for l in lines[line_idx + 1: line_idx + 6] if l.strip()]
                    if sample_data_lines:
                        matching_rows = 0
                        numeric_cells = 0
                        total_cells = 0
                        for dl in sample_data_lines:
                            dl_parts = dl.split()
                            if len(dl_parts) == len(parts):
                                matching_rows += 1
                                for dp in dl_parts:
                                    total_cells += 1
                                    if re.match(r"^-?\d+(\.\d+)?$", dp) or dp in MISSING_VALUE_MARKERS:
                                        numeric_cells += 1

                        if matching_rows >= 2 and total_cells > 0 and (numeric_cells / total_cells) >= 0.4:
                            best_delimiter = r"\s+"
                            best_header_idx = line_idx
                            best_columns = parts
                            break

    return best_delimiter, best_header_idx, best_columns


def parse_cmlre_txt(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Master parser for CMLRE TXT and delimited datasets.
    """
    encoding = detect_file_encoding(file_path)

    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        content = f.read()

    lines = content.splitlines()
    if not lines or not any(l.strip() for l in lines):
        raise ValueError(f"File is empty: {file_path}")

    # 1. Extract metadata & preambles
    metadata, start_idx = extract_preamble_metadata(lines)

    # 2. Detect delimiter and header
    delimiter, header_idx, raw_headers = detect_delimiter_and_header(lines, start_idx)

    if delimiter is None or not raw_headers:
        raise ValueError(
            "Could not identify a consistent tabular structure. "
            "Detected metadata/header candidates but no valid tabular data rows."
        )

    # 3. Construct clean tabular stream starting from header
    table_text = "\n".join(lines[header_idx:])
    
    # 4. Parse into DataFrame using pandas engine
    try:
        if delimiter == r"\s+":
            df = pd.read_csv(
                io.StringIO(table_text),
                sep=r"\s+",
                engine="python",
                na_values=list(MISSING_VALUE_MARKERS),
                keep_default_na=True
            )
        else:
            df = pd.read_csv(
                io.StringIO(table_text),
                sep=delimiter,
                engine="c",
                na_values=list(MISSING_VALUE_MARKERS),
                keep_default_na=True,
                low_memory=False
            )
    except Exception:
        df = pd.read_csv(
            io.StringIO(table_text),
            sep=delimiter if delimiter != r"\s+" else r"\s+",
            engine="python",
            na_values=list(MISSING_VALUE_MARKERS),
            keep_default_na=True
        )

    if df is None or len(df) == 0:
        raise ValueError(
            "Could not identify a consistent tabular structure. "
            "No data rows found below table header."
        )

    # Clean column headers
    df.columns = [str(c).strip().strip('"\'') for c in df.columns]

    # Replace missing value strings
    for col in df.columns:
        if df[col].dtype == object or str(df[col].dtype).startswith("str") or str(df[col].dtype).startswith("String"):
            df[col] = df[col].apply(lambda v: None if v is not None and str(v).strip() in MISSING_VALUE_MARKERS else v)

    diagnostics = {
        "encoding": encoding,
        "delimiter": delimiter,
        "header_line_index": header_idx,
        "preamble_lines_count": header_idx,
        "raw_columns_count": len(df.columns),
        "raw_rows_count": len(df)
    }

    return df, metadata, diagnostics
