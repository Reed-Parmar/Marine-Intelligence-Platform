"""
Unit tests for Phase 4: Data Quality and Standardisation Pipeline.
Tests all 10+ required validation, transformation, scoring, and edge cases
with strict scientific timezone and unit validation rules.
"""

import unittest
from datetime import datetime
from typing import Any, Dict, List

from data_pipeline.models import IssueSeverity, QualityStatus
from data_pipeline.pipeline import QualityPipeline


class TestQualityPipeline(unittest.TestCase):
    """Test suite covering the core validation and standardisation scenarios."""

    def setUp(self):
        self.pipeline = QualityPipeline()

    def test_01_clean_dataset(self):
        """1. Clean dataset: Ideal CTD oceanographic records should score near 100 with PASSED status."""
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

    def test_02_missing_values(self):
        """2. Missing values: Detects null, empty string, -999, and whitespace markers."""
        data_with_missing = [
            {"time": "2026-03-15", "latitude": 10.0, "longitude": 76.0, "temperature": 28.0, "salinity": "-999"},
            {"time": "2026-03-15", "latitude": 10.1, "longitude": 76.1, "temperature": None, "salinity": 35.2},
            {"time": "2026-03-15", "latitude": 10.2, "longitude": 76.2, "temperature": "   ", "salinity": "NA"},
            {"time": "2026-03-15", "latitude": 10.3, "longitude": 76.3, "temperature": 27.5, "salinity": 35.4}
        ]
        result = self.pipeline.process(data_with_missing)
        
        # Check that -999, None, '   ', and 'NA' were converted to None
        self.assertIsNone(result.standardised_records[0]["salinity"])
        self.assertIsNone(result.standardised_records[1]["temperature"])
        self.assertIsNone(result.standardised_records[2]["temperature"])
        self.assertIsNone(result.standardised_records[2]["salinity"])
        self.assertGreater(result.summary.missing_count, 0)
        
        # Raw records must remain untampered
        self.assertEqual(result.raw_records[0]["salinity"], "-999")

    def test_03_duplicate_detection(self):
        """3. Duplicates: Identifies exact duplicate rows and logical marine key duplicates."""
        data_with_dups = [
            {"time": "2026-03-15T08:00:00Z", "latitude": 10.0, "longitude": 76.0, "depth": 10.0, "temperature": 28.0},
            {"time": "2026-03-15T08:00:00Z", "latitude": 10.0, "longitude": 76.0, "depth": 10.0, "temperature": 28.0},  # Exact duplicate
            {"time": "2026-03-15T08:00:00Z", "latitude": 10.0, "longitude": 76.0, "depth": 10.0, "temperature": 28.05}, # Logical key collision
            {"time": "2026-03-15T09:00:00Z", "latitude": 10.1, "longitude": 76.1, "depth": 15.0, "temperature": 27.5}
        ]
        result = self.pipeline.process(data_with_dups)
        
        self.assertGreaterEqual(result.summary.duplicate_count, 2)
        # Verify provenance was recorded and rows were flagged rather than deleted
        self.assertEqual(len(result.standardised_records), 4)

    def test_04_coordinate_validation(self):
        """4. Coordinates: Flags impossible latitudes (> 90) or longitudes (< -180) and invalid formats."""
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

    def test_05_timestamp_validation(self):
        """5. Timestamps: Tests timezone-aware, timezone-less, explicit UTC, and offset timestamps."""
        data_timestamps = [
            {"time": "15/03/2026 08:30:00", "latitude": 10.0, "longitude": 76.0},      # Naive DD/MM/YYYY HH:MM:SS -> preserves naive without 'Z'
            {"time": "2026-03-15", "latitude": 10.1, "longitude": 76.1},               # Naive YYYY-MM-DD
            {"time": "2026-03-15T08:30:00Z", "latitude": 10.2, "longitude": 76.2},     # Explicit UTC -> '...Z'
            {"time": "2026-03-15 08:30:00 UTC", "latitude": 10.3, "longitude": 76.3}, # Explicit UTC string -> '...Z'
            {"time": "2026-03-15T14:00:00+05:30", "latitude": 10.4, "longitude": 76.4}, # Explicit offset (+05:30) -> normalized to UTC (08:30:00Z)
            {"time": "not_a_date", "latitude": 10.5, "longitude": 76.5},               # Unparseable (error)
            {"time": "1750-01-01", "latitude": 10.6, "longitude": 76.6}                # Year < 1800 (error)
        ]
        result = self.pipeline.process(data_timestamps)
        
        # 1. Naive timestamp: preserved without appending 'Z'
        self.assertEqual(result.standardised_records[0]["time"], "2026-03-15T08:30:00")
        self.assertEqual(result.standardised_records[1]["time"], "2026-03-15")
        
        # Check that an INFO issue is recorded for naive timestamps
        tz_issues = [i for i in result.validation_issues if i.check == "timestamp_timezone"]
        self.assertGreaterEqual(len(tz_issues), 2)
        self.assertEqual(tz_issues[0].details.get("timezone_status"), "unknown")

        # 2. Explicit UTC timestamps
        self.assertEqual(result.standardised_records[2]["time"], "2026-03-15T08:30:00Z")
        self.assertEqual(result.standardised_records[3]["time"], "2026-03-15T08:30:00Z")

        # 3. Explicit non-UTC timezone (+05:30) converted to UTC
        self.assertEqual(result.standardised_records[4]["time"], "2026-03-15T08:30:00Z")

        # 4. Error counts
        self.assertEqual(result.summary.invalid_timestamps_count, 2)

    def test_06_scientific_range_checks(self):
        """6. Range checks: Identifies impossible errors (e.g. depth < 0) vs unusual warnings."""
        data_ranges = [
            {"time": "2026-03-15", "latitude": 10.0, "longitude": 76.0, "depth": -50.0, "temperature": 28.0}, # Negative depth (impossible)
            {"time": "2026-03-15", "latitude": 10.1, "longitude": 76.1, "depth": 10.0, "temperature": 65.0},  # 65°C ocean water (impossible)
            {"time": "2026-03-15", "latitude": 10.2, "longitude": 76.2, "depth": 10.0, "temperature": 36.5},  # 36.5°C tropical pool (unusual warning)
            {"time": "2026-03-15", "latitude": 10.3, "longitude": 76.3, "depth": 10.0, "temperature": 28.0}   # Normal
        ]
        result = self.pipeline.process(data_ranges)
        
        self.assertEqual(result.summary.range_violations_count, 2)
        impossible_issues = [i for i in result.validation_issues if i.check == "range_check_impossible"]
        unusual_issues = [i for i in result.validation_issues if i.check == "range_check_unusual"]
        self.assertEqual(len(impossible_issues), 2)
        self.assertGreaterEqual(len(unusual_issues), 1)

    def test_07_outlier_detection(self):
        """7. Outliers: Statistical IQR method flags anomalous values with details."""
        # 10 records with salinity around 35.0 PSU and one severe outlier at 44.8 PSU
        sal_data = [
            {"time": f"2026-03-15T0{i}:00:00Z", "latitude": 10.0, "longitude": 76.0, "salinity": 35.0 + (i * 0.05)}
            for i in range(9)
        ]
        sal_data.append({"time": "2026-03-15T09:00:00Z", "latitude": 10.0, "longitude": 76.0, "salinity": 44.8}) # Outlier
        
        result = self.pipeline.process(sal_data)
        
        self.assertGreaterEqual(result.summary.outliers_count, 1)
        outlier_issues = [i for i in result.validation_issues if i.check == "statistical_outlier_iqr"]
        self.assertTrue(any(i.column == "salinity" and i.value == 44.8 for i in outlier_issues))

    def test_08_unit_conversion_explicit(self):
        """8. Unit conversion: Converts Fahrenheit, feet, and mL/L ONLY when source units are explicitly known."""
        pipeline_units = QualityPipeline(
            unit_hints={"temperature": "fahrenheit", "depth": "feet", "dissolved_oxygen": "ml/l"}
        )
        data_units = [
            {"time": "2026-03-15", "latitude": 10.0, "longitude": 76.0, "temperature": 86.0, "depth": 100.0, "dissolved_oxygen": 5.0}
        ]
        result = pipeline_units.process(data_units)
        
        # 86°F = 30°C
        self.assertAlmostEqual(result.standardised_records[0]["temperature"], 30.0, places=1)
        # 100 ft = 30.48 m
        self.assertAlmostEqual(result.standardised_records[0]["depth"], 30.48, places=2)
        # 5.0 mL/L * 1.42903 = 7.145 mg/L
        self.assertAlmostEqual(result.standardised_records[0]["dissolved_oxygen"], 7.145, places=2)
        
        # Check that provenance records the transformations
        transforms = result.provenance["transformation_summary"]["sample_transformations"]
        self.assertGreaterEqual(len(transforms), 3)

    def test_09_dissolved_oxygen_unspecified_unit(self):
        """9. Dissolved Oxygen: Does NOT infer or convert mL/L when unit is not explicitly specified."""
        pipeline_no_hints = QualityPipeline()  # No unit hints
        data = [
            {"time": "2026-03-15", "latitude": 10.0, "longitude": 76.0, "dissolved_oxygen": 5.0}
        ]
        result = pipeline_no_hints.process(data)
        
        # Value must remain 5.0 (untouched), NOT converted with 1.42903
        self.assertEqual(result.standardised_records[0]["dissolved_oxygen"], 5.0)

    def test_10_schema_mapping(self):
        """10. Schema mapping: Maps alias column names to standard internal field names."""
        raw_headers_data = [
            {"LAT": 9.93, "LONG": 76.26, "DATE_TIME": "2026-03-15T08:00:00Z", "SST": 28.5, "DO_mgL": 6.1, "STN_NO": "CMLRE-01"}
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

    def test_11_mixed_dataset_end_to_end(self):
        """11. Mixed-quality dataset: Evaluates QC scoring, QC criteria wording in notes, and Postgres update payload."""
        mixed_data = [
            {"Lat": 9.93, "Lon": 76.26, "Time": "2026-03-15 08:00", "Temp": 28.5, "Salinity": 35.2},
            {"Lat": 9.94, "Lon": 76.27, "Time": "2026-03-15 08:30", "Temp": "-999", "Salinity": 35.3}, # Missing temp
            {"Lat": 105.0, "Lon": 76.28, "Time": "2026-03-15 09:00", "Temp": 28.1, "Salinity": 35.1}, # Invalid lat
            {"Lat": 9.95, "Lon": 76.29, "Time": "invalid_date", "Temp": 28.0, "Salinity": 35.4},     # Invalid time
            {"Lat": 9.96, "Lon": 76.30, "Time": "2026-03-15 10:00", "Temp": 70.0, "Salinity": 35.2}  # Range error (70°C)
        ]
        result = self.pipeline.process(mixed_data, {"dataset_id": "d1a2b3c4-test", "domain_type": "oceanography"})
        
        # Should be FLAGGED or FAILED due to range and coordinate errors
        self.assertIn(result.quality_status, (QualityStatus.FLAGGED, QualityStatus.FAILED))
        self.assertLess(result.quality_score, 85.0)
        
        # Verify JSON serialization
        result_dict = result.to_dict()
        self.assertIn("quality_score", result_dict)
        self.assertIn("provenance", result_dict)
        
        # Verify Postgres datasets table update payload
        pg_payload = result.to_postgres_dataset_update()
        self.assertIn("quality_score", pg_payload)
        self.assertIn("quality_status", pg_payload)
        self.assertIn("validation_notes", pg_payload)
        self.assertIn("provenance_metadata", pg_payload)
        self.assertIsInstance(pg_payload["validation_notes"], str)
        self.assertIn("predefined QC criteria", pg_payload["validation_notes"])


if __name__ == "__main__":
    unittest.main()
