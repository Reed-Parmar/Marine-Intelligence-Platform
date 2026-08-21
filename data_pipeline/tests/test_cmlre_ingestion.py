"""
Comprehensive Test Suite for Phase 3 CMLRE Data Ingestion Engine.
Tests all real CMLRE datasets, format detection, preambles, delimiters,
missing values, column normalization, canonical CSV/XLSX export, and Phase 4 boundary.
"""

import os
import shutil
import sys
from pathlib import Path
import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_pipeline.ingestion.canonical_exporter import export_canonical_csv, export_canonical_xlsx
from data_pipeline.ingestion.format_detector import classify_domain, detect_format_and_preview
from data_pipeline.ingestion.ingestion_manager import process_upload
from data_pipeline.ingestion.schema_normalizer import normalize_dataframe_columns
from data_pipeline.ingestion.txt_parser import detect_delimiter_and_header, extract_preamble_metadata, parse_cmlre_txt
from data_pipeline.quality_standardisation.phase4_boundary import integrate_with_phase4

DATASET_DIR = ROOT_DIR / "dataset"
TEST_TMP_DIR = ROOT_DIR / "data_pipeline" / "tests" / "_tmp_test"


@pytest.fixture
def temp_dir():
    os.makedirs(TEST_TMP_DIR, exist_ok=True)
    yield str(TEST_TMP_DIR)
    shutil.rmtree(TEST_TMP_DIR, ignore_errors=True)


# 1. Real CMLRE Dataset Tests
@pytest.mark.parametrize("filename, expected_domain, min_rows, min_cols", [
    ("dnaderiveddata1.txt", "edna", 10, 15),
    ("occurrence.txt", "biodiversity", 1000, 25),
    ("occurrence1.txt", "biodiversity", 500, 20),
    ("occurrence2.txt", "biodiversity", 2000, 25),
    ("occurrence3.txt", "biodiversity", 5000, 20),
])
def test_real_cmlre_dataset_parsing(filename, expected_domain, min_rows, min_cols):
    """Verifies that all real CMLRE datasets in dataset/ are parsed accurately."""
    file_path = str(DATASET_DIR / filename)
    if not os.path.exists(file_path):
        pytest.skip(f"Dataset file {filename} not present")

    df, meta, diag = parse_cmlre_txt(file_path)
    assert df is not None
    assert len(df) >= min_rows, f"Expected at least {min_rows} rows, got {len(df)}"
    assert len(df.columns) >= min_cols, f"Expected at least {min_cols} columns, got {len(df.columns)}"

    domain = classify_domain(list(df.columns))
    assert domain == expected_domain, f"Expected {expected_domain}, got {domain}"


# 2. Preamble & CTD Metadata Extraction Test
def test_cmlre_ctd_preamble_and_table(temp_dir):
    """Tests CTD dataset with header comments, cruise metadata, and tabular stream."""
    content = (
        "* Sea-Bird SBE 19plus CTD Data File:\n"
        "* Cruise_Name = FORV Sagar Sampada SS404\n"
        "* Station_Number = STN_01\n"
        "* Latitude = 09 21.60 N\n"
        "* Longitude = 075 29.90 E\n"
        "* Date = 2024-03-22\n"
        "*END*\n"
        "depth\ttemperature\tsalinity\tdissolved_oxygen\tchlorophyll\n"
        "0.0\t28.52\t35.21\t4.82\t0.35\n"
        "10.0\t28.15\t35.32\t4.75\t0.42\n"
        "20.0\t27.80\t35.45\t4.50\t0.65\n"
    )
    file_path = os.path.join(temp_dir, "ctd_ss404.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    df, meta, diag = parse_cmlre_txt(file_path)
    assert len(df) == 3
    assert list(df.columns) == ["depth", "temperature", "salinity", "dissolved_oxygen", "chlorophyll"]
    assert meta.get("cruise_name") == "FORV Sagar Sampada SS404"
    assert meta.get("station_number") == "STN_01"


# 3. Semicolon-Delimited Fisheries Log Test
def test_cmlre_fisheries_semicolon_delimited(temp_dir):
    """Tests fisheries log using semicolon delimiter with metadata."""
    content = (
        "# CMLRE Bottom Trawl Survey Log\n"
        "# Vessel: FORV Sagar Sampada | Gear: HOBT\n"
        "recorded_at;fishing_zone;gear_type;effort_hours;scientific_name;catch_weight_kg\n"
        "2024-04-10;Arabian Sea EEZ;HOBT;3.5;Nemipterus japonicus;142.5\n"
        "2024-04-10;Arabian Sea EEZ;HOBT;3.5;Decapterus russelli;89.0\n"
    )
    file_path = os.path.join(temp_dir, "fisheries_log.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    df, meta, diag = parse_cmlre_txt(file_path)
    assert len(df) == 2
    assert "scientific_name" in df.columns
    assert "catch_weight_kg" in df.columns
    assert diag["delimiter"] == ";"


# 4. Whitespace-Delimited Tabular Data Test
def test_whitespace_delimited_dataset(temp_dir):
    """Tests tabular dataset with variable whitespace delimiters."""
    content = (
        "Depth    Temp      Salinity    DO\n"
        "0.0      28.52     35.21       4.82\n"
        "10.0     28.15     35.32       4.75\n"
        "20.0     27.80     35.45       4.50\n"
    )
    file_path = os.path.join(temp_dir, "space_data.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    df, meta, diag = parse_cmlre_txt(file_path)
    assert len(df) == 3
    assert len(df.columns) == 4
    assert diag["delimiter"] == r"\s+"


# 5. Missing Value Markers Normalization
def test_missing_value_markers_normalization(temp_dir):
    """Verifies that standard missing value markers (-999, NA, ND, null) become null/None."""
    content = (
        "station_id\tdepth\ttemperature\tsalinity\tdissolved_oxygen\n"
        "STN1\t0.0\t28.5\t35.2\t-999\n"
        "STN2\t10.0\tNA\t35.3\t4.5\n"
        "STN3\t20.0\t27.8\tND\tnull\n"
    )
    file_path = os.path.join(temp_dir, "missing_val_data.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    df, meta, diag = parse_cmlre_txt(file_path)
    assert len(df) == 3
    assert pd.isna(df.loc[0, "dissolved_oxygen"]) or df.loc[0, "dissolved_oxygen"] is None
    assert pd.isna(df.loc[1, "temperature"]) or df.loc[1, "temperature"] is None
    assert pd.isna(df.loc[2, "salinity"]) or df.loc[2, "salinity"] is None


# 6. Schema Normalization & Column Preservation
def test_schema_normalization_preserves_unmapped_columns():
    """Verifies that Darwin Core aliases normalize to canonical names without losing custom columns."""
    df_raw = pd.DataFrame({
        "decimalLatitude": [9.36, 9.37],
        "decimalLongitude": [75.49, 75.50],
        "minimumDepthInMeters": [20.0, 30.0],
        "eventDate": ["2024-03-22", "2024-03-23"],
        "scientificName": ["Larus michahellis", "Oryzias latipes"],
        "pcr_primer_forward": ["TCAACCAACCA", "TAGACTTCTGG"],
        "custom_sensor_id": ["SBE-99", "SBE-100"]
    })

    norm_df, mappings = normalize_dataframe_columns(df_raw)
    assert "latitude" in norm_df.columns
    assert "longitude" in norm_df.columns
    assert "depth" in norm_df.columns
    assert "timestamp" in norm_df.columns
    assert "scientific_name" in norm_df.columns
    assert "pcr_primer_forward" in norm_df.columns
    assert "custom_sensor_id" in norm_df.columns
    assert len(norm_df.columns) == 7


# 7. Non-Tabular Text Graceful Rejection
def test_non_tabular_txt_graceful_rejection(temp_dir):
    """Verifies that unstructured prose narrative is gracefully rejected."""
    content = (
        "FORV Sagar Sampada Cruise Narrative Report\n"
        "Date: 22nd March 2024\n"
        "The vessel departed Kochi harbor at dawn with clear skies.\n"
        "Sea state was calm with minor swells.\n"
        "All scientific equipment was calibrated successfully.\n"
    )
    file_path = os.path.join(temp_dir, "cruise_report.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    with pytest.raises(ValueError) as exc_info:
        parse_cmlre_txt(file_path)
    assert "Could not identify a consistent tabular structure" in str(exc_info.value)


# 8. Canonical CSV & XLSX Round-Trip Test
def test_canonical_csv_and_xlsx_round_trip(temp_dir):
    """Verifies that generated canonical CSV and XLSX can be read back with exact row/col fidelity."""
    sample_df = pd.DataFrame({
        "latitude": [9.93, 9.94, 9.95],
        "longitude": [76.26, 76.27, 76.28],
        "depth": [10.0, 20.0, 30.0],
        "temperature": [28.5, 28.2, 27.9],
        "salinity": [35.2, 35.3, 35.5]
    })
    meta = {"cruise": "SS404", "station": "STN-01"}

    csv_path = os.path.join(temp_dir, "canonical_test.csv")
    xlsx_path = os.path.join(temp_dir, "canonical_test.xlsx")

    export_canonical_csv(sample_df, csv_path)
    export_canonical_xlsx(sample_df, xlsx_path, metadata=meta)

    # CSV Round-trip
    read_csv_df = pd.read_csv(csv_path)
    assert len(read_csv_df) == 3
    assert list(read_csv_df.columns) == list(sample_df.columns)

    # XLSX Round-trip
    read_xlsx_df = pd.read_excel(xlsx_path, sheet_name="Data")
    assert len(read_xlsx_df) == 3
    read_meta_df = pd.read_excel(xlsx_path, sheet_name="Metadata")
    assert len(read_meta_df) == 2


# 9. Phase 4 Integration Boundary Test
def test_phase4_integration_boundary():
    """Verifies that integrate_with_phase4 accepts canonical df and returns clean structured QC dict."""
    canonical_df = pd.DataFrame({
        "latitude": [10.5, 10.6],
        "longitude": [72.2, 72.3],
        "depth": [15.0, 25.0],
        "temperature": [28.4, 28.1],
        "salinity": [35.1, 35.3]
    })
    meta = {"domain_type": "oceanography", "source_filename": "test.txt"}

    res = integrate_with_phase4(canonical_df, dataset_metadata=meta)
    assert "df" in res
    assert "quality_status" in res
    assert "validation_notes" in res
    assert "provenance" in res
    assert len(res["df"]) == 2


# 10. End-to-End Ingestion Manager Orchestration Test
def test_end_to_end_ingestion_manager(temp_dir):
    """Verifies complete orchestration: detection -> normalization -> canonical export -> registration."""
    content = (
        "timestamp\tdecimalLatitude\tdecimalLongitude\ttemp_c\tsalinity\n"
        "2026-08-20T10:00:00Z\t15.5\t72.1\t28.5\t35.2\n"
        "2026-08-20T11:00:00Z\t15.6\t72.2\t28.7\t35.4\n"
    )
    raw_path = os.path.join(temp_dir, "raw_ocean_survey.txt")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(content)

    res = process_upload(
        raw_path,
        dataset_name="End-to-End Ingestion Test",
        export_canonical=True,
        export_xlsx=True,
        output_dir=temp_dir
    )
    assert res["status"] == "success"
    assert res["domain_type"] == "oceanography"
    assert res["row_count"] == 2
    assert "latitude" in res["columns"]
    assert "temperature" in res["columns"]
    assert os.path.exists(res["canonical_csv_path"])
    assert os.path.exists(res["canonical_xlsx_path"])
