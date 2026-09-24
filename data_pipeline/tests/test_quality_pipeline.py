"""
Comprehensive Test Suite for Phase 4: Data Quality & Scientific Standardisation.
Covers all required validation scenarios (A - L) and real CMLRE datasets from dataset/.
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = ROOT_DIR / "dataset"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_pipeline.ingestion.schema_normalizer import normalize_dataframe_columns
from data_pipeline.ingestion.txt_parser import parse_cmlre_txt
from data_pipeline.quality_standardisation.models import (
    DatasetQualityResult,
    IssueSeverity,
    QualityScoreSummary,
    QualityStatus,
    ValidationIssue,
)
from data_pipeline.quality_standardisation.phase4_boundary import integrate_with_phase4
from data_pipeline.quality_standardisation.pipeline import QualityPipeline
from data_pipeline.quality_standardisation.schema_mapper import SchemaMapper
from data_pipeline.quality_standardisation.unit_converter import UnitConverter


class TestPhase4DataQualityStandardisation(unittest.TestCase):
    """Full test suite covering Phase 4 Quality & Standardisation responsibilities."""

    def setUp(self):
        self.pipeline = QualityPipeline()

    # =========================================================================
    # A. Clean Oceanographic Dataset Test
    # =========================================================================
    def test_A_clean_oceanographic_dataset(self):
        """A. Clean dataset: Ideal CTD oceanographic records should score >= 95 with PASSED status."""
        clean_data = [
            {"time": "2026-03-15T08:30:00Z", "latitude": 9.9312, "longitude": 76.2673, "depth": 10.5, "temperature": 28.4, "salinity": 35.1, "dissolved_oxygen": 6.2},
            {"time": "2026-03-15T09:00:00Z", "latitude": 9.9350, "longitude": 76.2710, "depth": 25.0, "temperature": 27.8, "salinity": 35.3, "dissolved_oxygen": 5.9},
            {"time": "2026-03-15T09:30:00Z", "latitude": 9.9400, "longitude": 76.2750, "depth": 50.0, "temperature": 26.5, "salinity": 35.6, "dissolved_oxygen": 5.2},
            {"time": "2026-03-15T10:00:00Z", "latitude": 9.9450, "longitude": 76.2800, "depth": 75.0, "temperature": 24.1, "salinity": 35.8, "dissolved_oxygen": 4.8},
            {"time": "2026-03-15T10:30:00Z", "latitude": 9.9500, "longitude": 76.2850, "depth": 100.0, "temperature": 22.3, "salinity": 36.0, "dissolved_oxygen": 4.1}
        ]
        result = self.pipeline.process(clean_data, {"domain_type": "oceanography"})
        
        self.assertEqual(result.quality_status, QualityStatus.PASSED)
        self.assertGreaterEqual(result.quality_score, 95.0)
        self.assertEqual(len(result.standardised_records), 5)
        self.assertEqual(result.summary.invalid_coords_count, 0)
        self.assertEqual(result.summary.invalid_timestamps_count, 0)
        self.assertEqual(result.summary.missing_count, 0)
        self.assertEqual(result.summary.duplicate_count, 0)

    # =========================================================================
    # B. Missing Values Test
    # =========================================================================
    def test_B_missing_values_normalization(self):
        """B. Missing values: Detects null, empty string, -999, NA, nil, and whitespace markers."""
        data_with_missing = [
            {"time": "2026-03-15", "latitude": 10.0, "longitude": 76.0, "temperature": 28.0, "salinity": "-999"},
            {"time": "2026-03-15", "latitude": 10.1, "longitude": 76.1, "temperature": None, "salinity": 35.2},
            {"time": "2026-03-15", "latitude": 10.2, "longitude": 76.2, "temperature": "   ", "salinity": "NA"},
            {"time": "2026-03-15", "latitude": 10.3, "longitude": 76.3, "temperature": 27.5, "salinity": "missing"}
        ]
        result = self.pipeline.process(data_with_missing)
        
        # Check that -999, None, '   ', 'NA', and 'missing' were converted to None
        self.assertIsNone(result.standardised_records[0]["salinity"])
        self.assertIsNone(result.standardised_records[1]["temperature"])
        self.assertIsNone(result.standardised_records[2]["temperature"])
        self.assertIsNone(result.standardised_records[2]["salinity"])
        self.assertIsNone(result.standardised_records[3]["salinity"])
        self.assertGreater(result.summary.missing_count, 0)
        
        # Raw records must remain untampered
        self.assertEqual(result.raw_records[0]["salinity"], "-999")

    # =========================================================================
    # C. Duplicate Records Test
    # =========================================================================
    def test_C_duplicate_records_detection(self):
        """C. Duplicates: Identifies exact duplicate rows and logical marine key collisions without deleting."""
        data_with_dups = [
            {"time": "2026-03-15T08:00:00Z", "latitude": 10.0, "longitude": 76.0, "depth": 10.0, "temperature": 28.0},
            {"time": "2026-03-15T08:00:00Z", "latitude": 10.0, "longitude": 76.0, "depth": 10.0, "temperature": 28.0},  # Exact duplicate
            {"time": "2026-03-15T08:00:00Z", "latitude": 10.0, "longitude": 76.0, "depth": 10.0, "temperature": 28.05}, # Logical key collision
            {"time": "2026-03-15T09:00:00Z", "latitude": 10.1, "longitude": 76.1, "depth": 15.0, "temperature": 27.5}
        ]
        result = self.pipeline.process(data_with_dups)
        
        self.assertGreaterEqual(result.summary.duplicate_count, 2)
        # Verify rows were flagged rather than deleted
        self.assertEqual(len(result.standardised_records), 4)

    # =========================================================================
    # D. Invalid Coordinates Test
    # =========================================================================
    def test_D_invalid_coordinates(self):
        """D. Coordinates: Flags impossible latitudes (> 90) or longitudes (< -180) and invalid formats."""
        data_invalid_coords = [
            {"time": "2026-03-15", "latitude": 95.5, "longitude": 76.0, "temperature": 28.0},    # Lat > 90
            {"time": "2026-03-15", "latitude": 10.0, "longitude": -195.0, "temperature": 28.0},  # Lon < -180
            {"time": "2026-03-15", "latitude": "invalid_lat", "longitude": 76.0, "temperature": 28.0},
            {"time": "2026-03-15", "latitude": 10.5, "longitude": 76.5, "temperature": 28.0}    # Valid
        ]
        result = self.pipeline.process(data_invalid_coords)
        
        self.assertEqual(result.summary.invalid_coords_count, 3)
        coord_errors = [i for i in result.validation_issues if i.check in ("coordinate_bounds", "coordinate_format")]
        self.assertEqual(len(coord_errors), 3)

    # =========================================================================
    # E. Timezone-Aware Timestamps Test
    # =========================================================================
    def test_E_timezone_aware_timestamps(self):
        """E. Timezone-aware timestamps: Normalizes explicit UTC ('Z', 'UTC') and offsets ('+05:30') to standard UTC."""
        data_tz_aware = [
            {"time": "2026-03-15T08:30:00Z", "latitude": 10.0, "longitude": 76.0},
            {"time": "2026-03-15 08:30:00 UTC", "latitude": 10.1, "longitude": 76.1},
            {"time": "2026-03-15T14:00:00+05:30", "latitude": 10.2, "longitude": 76.2}  # 14:00 IST = 08:30:00 UTC
        ]
        result = self.pipeline.process(data_tz_aware)
        
        self.assertEqual(result.standardised_records[0]["time"], "2026-03-15T08:30:00Z")
        self.assertEqual(result.standardised_records[1]["time"], "2026-03-15T08:30:00Z")
        self.assertEqual(result.standardised_records[2]["time"], "2026-03-15T08:30:00Z")

    # =========================================================================
    # F. Timezone-Less Timestamps Test
    # =========================================================================
    def test_F_timezone_less_timestamps(self):
        """F. Timezone-less timestamps: Preserves naive representation without assuming UTC/IST, recording INFO note."""
        data_naive = [
            {"time": "2026-03-15 08:30:00", "latitude": 10.0, "longitude": 76.0},
            {"time": "15/03/2026 08:30:00", "latitude": 10.1, "longitude": 76.1},
            {"time": "2026-03-15", "latitude": 10.2, "longitude": 76.2}
        ]
        result = self.pipeline.process(data_naive)
        
        # Must preserve naive format without appending 'Z'
        self.assertEqual(result.standardised_records[0]["time"], "2026-03-15T08:30:00")
        self.assertEqual(result.standardised_records[1]["time"], "2026-03-15T08:30:00")
        self.assertEqual(result.standardised_records[2]["time"], "2026-03-15")
        
        # Must record an INFO validation issue regarding unknown timezone
        tz_issues = [i for i in result.validation_issues if i.check == "timestamp_timezone"]
        self.assertGreaterEqual(len(tz_issues), 3)
        self.assertEqual(tz_issues[0].severity, IssueSeverity.INFO)
        self.assertEqual(tz_issues[0].details.get("timezone_status"), "unknown")

    # =========================================================================
    # G. Scientific Range Violations Test
    # =========================================================================
    def test_G_scientific_range_violations(self):
        """G. Range checks: Distinguishes impossible errors (depth < 0, temp > 42) from unusual warnings (temp > 35)."""
        data_ranges = [
            {"time": "2026-03-15", "latitude": 10.0, "longitude": 76.0, "depth": -10.0, "temperature": 28.0}, # Negative depth (impossible ERROR)
            {"time": "2026-03-15", "latitude": 10.1, "longitude": 76.1, "depth": 10.0, "temperature": 65.0},  # 65°C ocean water (impossible ERROR)
            {"time": "2026-03-15", "latitude": 10.2, "longitude": 76.2, "depth": 10.0, "temperature": 36.5},  # 36.5°C tropical tidepool (unusual WARNING)
            {"time": "2026-03-15", "latitude": 10.3, "longitude": 76.3, "depth": 10.0, "temperature": 28.0}   # Normal
        ]
        result = self.pipeline.process(data_ranges)
        
        self.assertEqual(result.summary.range_violations_count, 2)
        impossible_issues = [i for i in result.validation_issues if i.check == "range_check_impossible"]
        unusual_issues = [i for i in result.validation_issues if i.check == "range_check_unusual"]
        self.assertEqual(len(impossible_issues), 2)
        self.assertGreaterEqual(len(unusual_issues), 1)

    # =========================================================================
    # H. Statistical Outliers Test
    # =========================================================================
    def test_H_statistical_outliers_iqr(self):
        """H. Statistical outliers: Flags explainable IQR anomalies with details without deleting rows."""
        sal_data = [
            {"time": f"2026-03-15T0{i}:00:00Z", "latitude": 10.0, "longitude": 76.0, "salinity": 35.0 + (i * 0.05)}
            for i in range(9)
        ]
        sal_data.append({"time": "2026-03-15T09:00:00Z", "latitude": 10.0, "longitude": 76.0, "salinity": 44.8}) # Outlier
        
        result = self.pipeline.process(sal_data)
        
        self.assertGreaterEqual(result.summary.outliers_count, 1)
        outlier_issues = [i for i in result.validation_issues if i.check == "statistical_outlier_iqr"]
        self.assertTrue(any(i.column == "salinity" and i.value == 44.8 for i in outlier_issues))
        # Ensure row was retained
        self.assertEqual(len(result.standardised_records), 10)

    # =========================================================================
    # I. Explicit Unit Conversion Test
    # =========================================================================
    def test_I_explicit_unit_conversion(self):
        """I. Unit conversion: Converts Fahrenheit, feet, bar, and DMS coords ONLY when explicit unit hints are given."""
        pipeline_units = QualityPipeline(
            unit_hints={
                "temperature": "fahrenheit", 
                "depth": "feet", 
                "dissolved_oxygen": "ml/l",
                "pressure": "bar"
            }
        )
        data_units = [
            {
                "time": "2026-03-15", 
                "latitude": "09° 21' 36\" N", 
                "longitude": "076° 15' 00\" E", 
                "temperature": 86.0, 
                "depth": 100.0, 
                "dissolved_oxygen": 5.0,
                "pressure": 10.0
            }
        ]
        result = pipeline_units.process(data_units)
        rec = result.standardised_records[0]
        
        # DMS coords -> decimal degrees
        self.assertAlmostEqual(rec["latitude"], 9.36, places=2)
        self.assertAlmostEqual(rec["longitude"], 76.25, places=2)
        # 86°F = 30°C
        self.assertAlmostEqual(rec["temperature"], 30.0, places=1)
        # 100 ft = 30.48 m
        self.assertAlmostEqual(rec["depth"], 30.48, places=2)
        # 5.0 mL/L * 1.42903 = 7.145 mg/L
        self.assertAlmostEqual(rec["dissolved_oxygen"], 7.145, places=2)
        # 10 bar = 100 dbar
        self.assertAlmostEqual(rec["pressure"], 100.0, places=1)
        
        # Provenance audit records
        transforms = result.provenance["transformation_summary"]["sample_transformations"]
        self.assertGreaterEqual(len(transforms), 5)

    # =========================================================================
    # J. Unspecified Dissolved Oxygen Units Test
    # =========================================================================
    def test_J_unspecified_dissolved_oxygen_units(self):
        """J. Dissolved Oxygen: Does NOT infer or convert mL/L when unit is not explicitly specified."""
        pipeline_no_hints = QualityPipeline()
        data = [
            {"time": "2026-03-15", "latitude": 10.0, "longitude": 76.0, "dissolved_oxygen": 5.0}
        ]
        result = pipeline_no_hints.process(data)
        
        # Value must remain 5.0 (untouched), NOT multiplied by 1.42903
        self.assertEqual(result.standardised_records[0]["dissolved_oxygen"], 5.0)

    # =========================================================================
    # K. Schema Normalization & Preservation Test
    # =========================================================================
    def test_K_schema_normalization_and_preservation(self):
        """K. Schema mapping: Maps known aliases to canonical names and preserves unmapped domain fields."""
        raw_headers_data = [
            {
                "LAT": 9.93, 
                "LONG": 76.26, 
                "DATE_TIME": "2026-03-15T08:00:00Z", 
                "SST": 28.5, 
                "DO_mgL": 6.1, 
                "STN_NO": "CMLRE-01",
                "custom_edna_barcode": "ACTGTTACGA",
                "unmapped_gear_setting": "HOBT-v2"
            }
        ]
        result = self.pipeline.process(raw_headers_data)
        row = result.standardised_records[0]
        
        self.assertIn("latitude", row)
        self.assertIn("longitude", row)
        self.assertIn("time", row)
        self.assertIn("temperature", row)
        self.assertIn("dissolved_oxygen", row)
        self.assertIn("station", row)
        self.assertEqual(row["station"], "CMLRE-01")
        
        # Unmapped fields must be preserved intact
        self.assertIn("custom_edna_barcode", row)
        self.assertEqual(row["custom_edna_barcode"], "ACTGTTACGA")
        self.assertIn("unmapped_gear_setting", row)
        self.assertEqual(row["unmapped_gear_setting"], "HOBT-v2")
        self.assertIn("custom_edna_barcode", result.summary.unmapped_columns)

    # =========================================================================
    # L. End-to-End Phase 3 -> Phase 4 Integration Test
    # =========================================================================
    def test_L_phase3_to_phase4_end_to_end(self):
        """L. End-to-end integration: Tests Phase 3 canonical DataFrame flowing into Phase 4 QualityPipeline."""
        canonical_df = pd.DataFrame({
            "latitude": [9.93, 9.94, 9.95],
            "longitude": [76.26, 76.27, 76.28],
            "time": ["2026-03-15T08:00:00Z", "2026-03-15T09:00:00Z", "2026-03-15T10:00:00Z"],
            "depth": [10.0, 20.0, 30.0],
            "temperature": [28.5, 28.2, 27.9],
            "salinity": [35.2, 35.3, 35.5]
        })
        meta = {
            "dataset_id": "cmlre-test-001",
            "domain_type": "oceanography",
            "source_filename": "ctd_profile.txt"
        }
        
        res = integrate_with_phase4(canonical_df, dataset_metadata=meta)
        
        self.assertTrue(res["phase4_executed"])
        self.assertEqual(res["quality_status"], "passed")
        self.assertGreaterEqual(res["quality_score"], 90.0)
        self.assertEqual(len(res["df"]), 3)
        self.assertIn("predefined QC criteria", res["validation_notes"])
        self.assertEqual(res["provenance"]["dataset_id"], "cmlre-test-001")

    # =========================================================================
    # M. Real CMLRE Datasets Tests (all 5 files in dataset/)
    # =========================================================================
    def test_M_real_cmlre_datasets_in_dataset_folder(self):
        """M. Real CMLRE datasets: Verifies all 5 files in dataset/ undergo Phase 3 -> Phase 4 successfully."""
        dataset_files = [
            ("dnaderiveddata1.txt", "edna", 100),
            ("occurrence.txt", "biodiversity", 1500),
            ("occurrence1.txt", "biodiversity", 800),
            ("occurrence2.txt", "biodiversity", 2000),
            ("occurrence3.txt", "biodiversity", 10000)
        ]
        
        for filename, expected_domain, min_expected_rows in dataset_files:
            file_path = DATASET_DIR / filename
            if not file_path.exists():
                print(f"Skipping {filename} (not found)")
                continue
                
            # 1. Phase 3 parser
            raw_df, extracted_meta, diagnostics = parse_cmlre_txt(str(file_path))
            self.assertIsNotNone(raw_df, f"Failed to parse {filename}")
            self.assertGreaterEqual(len(raw_df), min_expected_rows)
            
            # 2. Phase 3 schema normalizer
            norm_df, applied_mappings = normalize_dataframe_columns(raw_df)
            self.assertEqual(len(norm_df), len(raw_df))
            
            # 3. Phase 4 Quality Pipeline via boundary
            meta = {
                "dataset_id": f"cmlre-{filename}",
                "domain_type": expected_domain,
                "source_filename": filename,
                "preambles": extracted_meta
            }
            res = integrate_with_phase4(norm_df, dataset_metadata=meta)
            
            self.assertTrue(res["phase4_executed"], f"Phase 4 did not execute for {filename}")
            self.assertIsNotNone(res["quality_score"], f"No quality score for {filename}")
            self.assertIn(res["quality_status"], ["passed", "flagged"], f"Unexpected status {res['quality_status']} for {filename}")
            self.assertEqual(len(res["df"]), len(raw_df), f"Row count mismatch in QC output for {filename}")
            self.assertIsInstance(res["validation_notes"], str)
            self.assertGreater(len(res["validation_notes"]), 20)


if __name__ == "__main__":
    unittest.main()
