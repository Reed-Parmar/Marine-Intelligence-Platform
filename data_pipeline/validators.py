"""
Scientific and data quality validators for Phase 4.
Implements missing value detection, duplicate detection, coordinate bounds,
timestamp parsing, scientific range checks, and IQR outlier detection.
"""

from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from data_pipeline.models import IssueSeverity, TransformationRecord, ValidationIssue


# Standard missing value tokens in oceanographic and scientific datasets
DEFAULT_MISSING_MARKERS: Set[str] = {
    "", " ", "  ", "   ", "nan", "null", "none", "na", "n/a", "nil",
    "-999", "-9999", "-999.0", "-9999.0", "-99.0", "-99", ".", "missing", "nd", "unknown"
}

# Documented scientific marine ranges and heuristic boundaries
# References: IOC/UNESCO QARTOD Oceanographic Data Manuals & WOD (World Ocean Database)
DEFAULT_RANGE_RULES: Dict[str, Dict[str, Any]] = {
    "temperature": {
        "unit": "°C",
        "min_possible": -2.5,   # Freezing point of seawater at high salinity/depth is ~ -2.0°C to -2.5°C
        "max_possible": 42.0,   # Extreme surface water in Persian Gulf / Red Sea / tropical tidepools ~36-40°C
        "min_warning": 0.0,     # Normal open ocean range lower bound
        "max_warning": 35.0,    # Normal tropical surface upper bound
        "description": "Seawater temperature in Celsius"
    },
    "salinity": {
        "unit": "PSU",
        "min_possible": 0.0,    # Estuaries / river discharge can reach 0.0 PSU
        "max_possible": 46.0,   # Persian Gulf / hypersaline lagoons can reach ~45 PSU
        "min_warning": 10.0,    # Typical marine lower threshold
        "max_warning": 42.0,    # Typical marine upper threshold
        "description": "Practical salinity in PSU"
    },
    "dissolved_oxygen": {
        "unit": "mg/L",
        "min_possible": 0.0,    # Anoxic bottom waters = 0.0 mg/L
        "max_possible": 25.0,   # Highly supersaturated surface phytoplankton blooms up to ~20-22 mg/L
        "min_warning": 0.5,     # Severe hypoxia threshold < 2.0 mg/L
        "max_warning": 15.0,    # Normal saturated ocean water is ~6-9 mg/L
        "description": "Dissolved oxygen concentration in mg/L"
    },
    "depth": {
        "unit": "m",
        "min_possible": 0.0,    # Surface = 0 m; negative values represent above sea surface/impossible depth
        "max_possible": 11500.0,# Challenger Deep maximum ocean depth is ~10,928 m
        "min_warning": 0.0,
        "max_warning": 6500.0,  # Abyssal ocean floor average
        "description": "Sampling or observation depth in meters"
    },
    "chlorophyll": {
        "unit": "mg/m³",
        "min_possible": 0.0,
        "max_possible": 150.0,  # Extreme red tide / algal blooms can reach >100 mg/m³
        "min_warning": 0.01,    # Oligotrophic open ocean
        "max_warning": 50.0,    # Coastal bloom warning threshold
        "description": "Chlorophyll-a concentration in mg/m³"
    },
    "ph": {
        "unit": "pH units",
        "min_possible": 6.0,    # Coastal acidic intrusion / vents
        "max_possible": 9.5,    # Hypersaline alkaline pools
        "min_warning": 7.3,     # Open ocean ocean acidification warning
        "max_warning": 8.6,     # Normal ocean surface ~8.1 - 8.3
        "description": "Seawater pH"
    },
    "pressure": {
        "unit": "dbar",
        "min_possible": 0.0,
        "max_possible": 13000.0,
        "min_warning": 0.0,
        "max_warning": 7000.0,
        "description": "Hydrostatic water pressure in decibars"
    },
    "catch_weight_kg": {
        "unit": "kg",
        "min_possible": 0.0,
        "max_possible": 500000.0, # Large commercial purse seine single haul
        "min_warning": 0.0,
        "max_warning": 50000.0,
        "description": "Fisheries catch weight in kilograms"
    },
    "effort_hours": {
        "unit": "hours",
        "min_possible": 0.0,
        "max_possible": 720.0,    # 30 days continuous cruise effort
        "min_warning": 0.1,
        "max_warning": 72.0,
        "description": "Fishing or sampling effort duration in hours"
    }
}


def is_missing_value(val: Any, custom_markers: Optional[Set[str]] = None) -> bool:
    """Checks whether a given field value represents a missing, null, or placeholder value."""
    if val is None:
        return True
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return True
    
    markers = custom_markers if custom_markers is not None else DEFAULT_MISSING_MARKERS
    str_val = str(val).strip().lower()
    return str_val in markers


class MissingValueValidator:
    """Detects missing values across fields and computes statistics without inventing/imputing values."""

    def __init__(self, custom_markers: Optional[Set[str]] = None):
        self.markers = custom_markers if custom_markers is not None else DEFAULT_MISSING_MARKERS

    def validate(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ValidationIssue], Dict[str, int], int]:
        """
        Scans records for missing values.
        Returns:
            - cleaned_records: records with missing representations normalized to None.
            - issues: ValidationIssue list for missing fields.
            - missing_counts_by_col: Dict mapping column name -> count of missing values.
            - total_missing: Total number of missing cells across entire dataset.
        """
        if not records:
            return [], [], {}, 0

        issues: List[ValidationIssue] = []
        cleaned_records: List[Dict[str, Any]] = []
        missing_by_col: Dict[str, int] = {}
        total_missing = 0
        total_rows = len(records)

        # Initialize counts for all columns
        all_cols = set()
        for r in records:
            all_cols.update(r.keys())
        for col in all_cols:
            missing_by_col[col] = 0

        for row_idx, row in enumerate(records):
            new_row = dict(row)
            for col, val in row.items():
                if is_missing_value(val, self.markers):
                    new_row[col] = None
                    missing_by_col[col] += 1
                    total_missing += 1
            cleaned_records.append(new_row)

        # Generate summary issues per column if missing values found
        for col, count in missing_by_col.items():
            if count > 0:
                pct = round((count / total_rows) * 100.0, 2)
                severity = IssueSeverity.ERROR if (col in ("latitude", "longitude", "time") and pct > 10.0) \
                    else IssueSeverity.WARNING if pct > 25.0 else IssueSeverity.INFO
                
                issues.append(
                    ValidationIssue(
                        check="missing_values",
                        column=col,
                        severity=severity,
                        message=f"Column '{col}' has {count} missing value(s) ({pct}% of dataset)",
                        details={"missing_count": count, "missing_percentage": pct}
                    )
                )

        return cleaned_records, issues, missing_by_col, total_missing


class DuplicateValidator:
    """Detects exact duplicate rows and logical key collisions while preserving provenance."""

    def __init__(self, key_columns: Optional[List[str]] = None):
        self.key_columns = key_columns

    def validate(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[ValidationIssue], int, Set[int]]:
        """
        Identifies duplicate rows.
        Returns:
            - issues: Validation issues for duplicates.
            - duplicate_count: Number of duplicate rows detected.
            - duplicate_indices: Set of 0-indexed row numbers that are duplicates of earlier rows.
        """
        if not records:
            return [], 0, set()

        seen_exact: Set[str] = set()
        seen_logical: Dict[Tuple, int] = {}
        duplicate_indices: Set[int] = set()
        issues: List[ValidationIssue] = []

        # Determine logical keys if present in records
        available_keys = []
        if self.key_columns:
            available_keys = self.key_columns
        else:
            # Default logical marine key: (time, latitude, longitude, depth, station, species)
            default_keys = ["time", "latitude", "longitude", "depth", "station", "species"]
            sample_keys = records[0].keys()
            available_keys = [k for k in default_keys if k in sample_keys]

        for idx, row in enumerate(records):
            # 1. Exact duplicate check
            # Create a sorted tuple representation of the row
            row_tuple = tuple(sorted((k, str(v) if v is not None else "") for k, v in row.items()))
            row_str = str(row_tuple)

            is_dup = False
            if row_str in seen_exact:
                duplicate_indices.add(idx)
                is_dup = True
            else:
                seen_exact.add(row_str)

            # 2. Logical duplicate check (if logical keys exist and row wasn't already an exact dup)
            if available_keys and not is_dup:
                logical_tuple = tuple(str(row.get(k, "")) for k in available_keys if row.get(k) is not None)
                if len(logical_tuple) >= 2 and all(v != "" for v in logical_tuple):
                    if logical_tuple in seen_logical:
                        first_seen_idx = seen_logical[logical_tuple]
                        duplicate_indices.add(idx)
                    else:
                        seen_logical[logical_tuple] = idx

        dup_count = len(duplicate_indices)
        if dup_count > 0:
            total_rows = len(records)
            pct = round((dup_count / total_rows) * 100.0, 2)
            issues.append(
                ValidationIssue(
                    check="duplicate_detection",
                    column="row",
                    severity=IssueSeverity.WARNING if pct < 15.0 else IssueSeverity.ERROR,
                    message=f"Detected {dup_count} duplicate record(s) ({pct}% of dataset)",
                    details={
                        "duplicate_count": dup_count,
                        "duplicate_percentage": pct,
                        "sample_duplicate_indices": list(sorted(duplicate_indices))[:20]
                    }
                )
            )

        return issues, dup_count, duplicate_indices


class CoordinateValidator:
    """Validates geographic latitude and longitude bounds and numeric consistency."""

    def validate(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ValidationIssue], List[TransformationRecord], int]:
        """
        Validates latitude ∈ [-90, 90] and longitude ∈ [-180, 180].
        Standardizes valid coordinates to float numbers.
        """
        if not records:
            return [], [], [], 0

        issues: List[ValidationIssue] = []
        transformations: List[TransformationRecord] = []
        validated_records: List[Dict[str, Any]] = []
        invalid_coords_count = 0

        for row_idx, row in enumerate(records):
            new_row = dict(row)
            lat_raw = row.get("latitude")
            lon_raw = row.get("longitude")

            # If latitude is present
            if lat_raw is not None:
                try:
                    lat_val = float(lat_raw)
                    if math.isnan(lat_val) or math.isinf(lat_val):
                        raise ValueError("NaN or Inf coordinate")
                    
                    if not (-90.0 <= lat_val <= 90.0):
                        invalid_coords_count += 1
                        issues.append(
                            ValidationIssue(
                                check="coordinate_bounds",
                                column="latitude",
                                severity=IssueSeverity.ERROR,
                                row_index=row_idx,
                                value=lat_raw,
                                expected="Latitude must be between -90.0 and 90.0 decimal degrees",
                                message=f"Row {row_idx}: Invalid latitude {lat_raw} is out of bounds [-90, 90]"
                            )
                        )
                    else:
                        new_row["latitude"] = lat_val
                        if not isinstance(lat_raw, (int, float)):
                            transformations.append(
                                TransformationRecord(
                                    column="latitude",
                                    row_index=row_idx,
                                    original_value=lat_raw,
                                    transformed_value=lat_val,
                                    rule="Parsed numeric latitude"
                                )
                            )
                except (ValueError, TypeError):
                    invalid_coords_count += 1
                    issues.append(
                        ValidationIssue(
                            check="coordinate_format",
                            column="latitude",
                            severity=IssueSeverity.ERROR,
                            row_index=row_idx,
                            value=lat_raw,
                            expected="Numeric decimal degrees",
                            message=f"Row {row_idx}: Non-numeric latitude value '{lat_raw}'"
                        )
                    )

            # If longitude is present
            if lon_raw is not None:
                try:
                    lon_val = float(lon_raw)
                    if math.isnan(lon_val) or math.isinf(lon_val):
                        raise ValueError("NaN or Inf coordinate")

                    if not (-180.0 <= lon_val <= 180.0):
                        invalid_coords_count += 1
                        issues.append(
                            ValidationIssue(
                                check="coordinate_bounds",
                                column="longitude",
                                severity=IssueSeverity.ERROR,
                                row_index=row_idx,
                                value=lon_raw,
                                expected="Longitude must be between -180.0 and 180.0 decimal degrees",
                                message=f"Row {row_idx}: Invalid longitude {lon_raw} is out of bounds [-180, 180]"
                            )
                        )
                    else:
                        new_row["longitude"] = lon_val
                        if not isinstance(lon_raw, (int, float)):
                            transformations.append(
                                TransformationRecord(
                                    column="longitude",
                                    row_index=row_idx,
                                    original_value=lon_raw,
                                    transformed_value=lon_val,
                                    rule="Parsed numeric longitude"
                                )
                            )
                except (ValueError, TypeError):
                    invalid_coords_count += 1
                    issues.append(
                        ValidationIssue(
                            check="coordinate_format",
                            column="longitude",
                            severity=IssueSeverity.ERROR,
                            row_index=row_idx,
                            value=lon_raw,
                            expected="Numeric decimal degrees",
                            message=f"Row {row_idx}: Non-numeric longitude value '{lon_raw}'"
                        )
                    )

            validated_records.append(new_row)

        return validated_records, issues, transformations, invalid_coords_count


class TimestampValidator:
    """
    Parses, validates, and standardizes timestamps.
    
    Timezone handling policy:
    - If explicit timezone is present (e.g. 'Z', '+05:30', 'UTC'): normalizes to ISO-8601 UTC ('...Z').
    - If no timezone is present (naive): preserves timestamp representation ('YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD')
      WITHOUT appending 'Z' or assuming UTC, and records a validation note (timezone unknown).
    - If an ISO-8601 date range interval is present (e.g. 'YYYY-MM-DD/YYYY-MM-DD'): parses and validates both endpoints.
    - If year-only (e.g. '2009') or year-month (e.g. '2009-02'): validates and standardizes as date.
    """

    KNOWN_NAIVE_FORMATS = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%Y-%m-%dT%H:%M:%S"
    ]

    def _parse_single_datetime(self, str_val: str) -> Tuple[Optional[datetime], bool, bool, bool]:
        """
        Parses a single datetime string.
        Returns: (parsed_dt, has_explicit_tz, is_utc, is_date_only)
        """
        str_clean = str(str_val).strip()
        str_upper = str_clean.upper()
        
        # 1. Year only (e.g. "2009")
        if re.match(r"^\d{4}$", str_clean):
            try:
                yr = int(str_clean)
                return datetime(yr, 1, 1), False, False, True
            except ValueError:
                pass

        # 2. Year-Month (e.g. "2009-02" or "2009/02")
        if re.match(r"^\d{4}[-\/]\d{1,2}$", str_clean):
            try:
                parts = re.split(r"[-\/]", str_clean)
                yr, mo = int(parts[0]), int(parts[1])
                if 1 <= mo <= 12:
                    return datetime(yr, mo, 1), False, False, True
            except ValueError:
                pass

        # 3. Explicit UTC/GMT marker
        if str_upper.endswith("Z") or " UTC" in str_upper or " GMT" in str_upper:
            cleaned_str = re.sub(r"\s*(UTC|GMT|Z)$", "", str_clean, flags=re.IGNORECASE).strip()
            try:
                dt = datetime.fromisoformat(cleaned_str.replace(" ", "T"))
                is_date_only = (dt.hour == 0 and dt.minute == 0 and dt.second == 0 and "T" not in cleaned_str and ":" not in cleaned_str)
                return dt.replace(tzinfo=timezone.utc), True, True, is_date_only
            except ValueError:
                for fmt in self.KNOWN_NAIVE_FORMATS:
                    try:
                        dt = datetime.strptime(cleaned_str, fmt).replace(tzinfo=timezone.utc)
                        is_date_only = ("%H" not in fmt and "%M" not in fmt)
                        return dt, True, True, is_date_only
                    except ValueError:
                        continue

        # 4. Explicit offset (+HH:MM, -HH:MM, +HHMM, -HHMM)
        elif re.search(r"[\+\-]\d{2}:?\d{2}$", str_clean):
            try:
                dt_with_tz = datetime.fromisoformat(str_clean.replace(" ", "T"))
                return dt_with_tz.astimezone(timezone.utc), True, True, False
            except ValueError:
                pass

        # 5. Naive standard ISO / known formats
        else:
            try:
                dt = datetime.fromisoformat(str_clean.replace(" ", "T"))
                is_date_only = (dt.hour == 0 and dt.minute == 0 and dt.second == 0 and "T" not in str_clean and ":" not in str_clean)
                return dt, False, False, is_date_only
            except ValueError:
                for fmt in self.KNOWN_NAIVE_FORMATS:
                    try:
                        dt = datetime.strptime(str_clean, fmt)
                        is_date_only = ("%H" not in fmt and "%M" not in fmt)
                        return dt, False, False, is_date_only
                    except ValueError:
                        continue

        return None, False, False, False

    def validate(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ValidationIssue], List[TransformationRecord], int]:
        """
        Standardizes 'time' / 'timestamp' column with strict timezone awareness.
        """
        if not records:
            return [], [], [], 0

        issues: List[ValidationIssue] = []
        transformations: List[TransformationRecord] = []
        validated_records: List[Dict[str, Any]] = []
        invalid_timestamps_count = 0
        current_year = datetime.now().year

        for row_idx, row in enumerate(records):
            new_row = dict(row)
            # Support both 'time' and 'timestamp' column keys
            time_col = "time" if "time" in row else ("timestamp" if "timestamp" in row else None)
            raw_time = row.get(time_col) if time_col else None

            if raw_time is not None and time_col is not None:
                parsed_dt: Optional[datetime] = None
                has_explicit_tz = False
                is_utc = False
                is_interval = False
                iso_str: Optional[str] = None
                rule_text = ""

                # 1. Check for ISO Date Interval (e.g. "2009-02-16/2009-02-23" or "2009/2010")
                if isinstance(raw_time, str) and "/" in raw_time and not re.search(r"^\d{1,2}/\d{1,2}/\d{2,4}", raw_time):
                    parts = raw_time.strip().split("/")
                    if len(parts) == 2:
                        dt_start, tz_start, utc_start, d_only_start = self._parse_single_datetime(parts[0])
                        dt_end, tz_end, utc_end, d_only_end = self._parse_single_datetime(parts[1])
                        if dt_start and dt_end:
                            if 1800 <= dt_start.year <= current_year + 1 and 1800 <= dt_end.year <= current_year + 1:
                                s1 = dt_start.strftime("%Y-%m-%d") if d_only_start else dt_start.strftime("%Y-%m-%dT%H:%M:%S")
                                s2 = dt_end.strftime("%Y-%m-%d") if d_only_end else dt_end.strftime("%Y-%m-%dT%H:%M:%S")
                                iso_str = f"{s1}/{s2}"
                                is_interval = True
                                rule_text = "Standardized ISO-8601 date range interval (start/end)"
                                parsed_dt = dt_start

                # 2. Already datetime instance
                if not is_interval:
                    if isinstance(raw_time, datetime):
                        if raw_time.tzinfo is not None:
                            parsed_dt = raw_time.astimezone(timezone.utc)
                            has_explicit_tz = True
                            is_utc = True
                        else:
                            parsed_dt = raw_time
                            has_explicit_tz = False
                        is_date_only = False

                    # 3. Numeric timestamp (unix seconds/millis, UTC by definition)
                    elif isinstance(raw_time, (int, float)):
                        try:
                            ts_val = raw_time / 1000.0 if raw_time > 1e11 else float(raw_time)
                            parsed_dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
                            has_explicit_tz = True
                            is_utc = True
                            is_date_only = False
                        except (ValueError, OSError, OverflowError):
                            parsed_dt = None
                            is_date_only = False

                    # 4. String representation
                    elif isinstance(raw_time, str):
                        parsed_dt, has_explicit_tz, is_utc, is_date_only = self._parse_single_datetime(raw_time)

                if parsed_dt is not None:
                    # Validate year reasonableness (1800 to next year)
                    if parsed_dt.year < 1800 or parsed_dt.year > current_year + 1:
                        invalid_timestamps_count += 1
                        issues.append(
                            ValidationIssue(
                                check="timestamp_range",
                                column=time_col,
                                severity=IssueSeverity.ERROR,
                                row_index=row_idx,
                                value=str(raw_time),
                                expected=f"Year must be between 1800 and {current_year + 1}",
                                message=f"Row {row_idx}: Impossible observation year {parsed_dt.year}"
                            )
                        )
                    else:
                        if not is_interval:
                            if has_explicit_tz and is_utc:
                                # Format as UTC with Z
                                iso_str = parsed_dt.strftime("%Y-%m-%d") if is_date_only else parsed_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                                rule_text = "Normalized timezone-aware timestamp to UTC"
                            else:
                                # Naive format WITHOUT 'Z' (preserves timestamp without inventing timezone)
                                iso_str = parsed_dt.strftime("%Y-%m-%d") if is_date_only else parsed_dt.strftime("%Y-%m-%dT%H:%M:%S")
                                rule_text = "Standardized naive timestamp (timezone unknown, preserved as-is)"
                                issues.append(
                                    ValidationIssue(
                                        check="timestamp_timezone",
                                        column=time_col,
                                        severity=IssueSeverity.INFO,
                                        row_index=row_idx,
                                        value=str(raw_time),
                                        expected="Explicit timezone offset or UTC marker",
                                        message=f"Row {row_idx}: Timestamp '{raw_time}' has no timezone information; preserved as naive local representation",
                                        details={"timezone_status": "unknown"}
                                    )
                                )

                        new_row[time_col] = iso_str
                        if iso_str != str(raw_time):
                            transformations.append(
                                TransformationRecord(
                                    column=time_col,
                                    row_index=row_idx,
                                    original_value=raw_time,
                                    transformed_value=iso_str,
                                    rule=rule_text
                                )
                            )
                else:
                    invalid_timestamps_count += 1
                    issues.append(
                        ValidationIssue(
                            check="timestamp_format",
                            column=time_col,
                            severity=IssueSeverity.ERROR,
                            row_index=row_idx,
                            value=str(raw_time),
                            expected="Valid ISO-8601 or standard date format (e.g. YYYY-MM-DD)",
                            message=f"Row {row_idx}: Unparseable timestamp '{raw_time}'"
                        )
                    )

            validated_records.append(new_row)

        return validated_records, issues, transformations, invalid_timestamps_count


class ScientificRangeValidator:
    """Validates numeric variables against documented scientific bounds."""

    def __init__(self, custom_rules: Optional[Dict[str, Dict[str, Any]]] = None):
        self.rules = dict(DEFAULT_RANGE_RULES)
        if custom_rules:
            self.rules.update(custom_rules)

    def validate(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[ValidationIssue], int]:
        """
        Executes scientific range checks.
        Distinguishes:
        - Critical/impossible errors (e.g. negative depth, salinity > 50 PSU)
        - Warning/unusual observations (e.g. tropical surface temp > 35°C)
        """
        if not records:
            return [], 0

        issues: List[ValidationIssue] = []
        violation_count = 0

        for row_idx, row in enumerate(records):
            for col, val in row.items():
                if val is None or col not in self.rules:
                    continue

                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    continue

                rule = self.rules[col]
                unit = rule.get("unit", "")
                min_pos = rule.get("min_possible")
                max_pos = rule.get("max_possible")
                min_warn = rule.get("min_warning")
                max_warn = rule.get("max_warning")

                # 1. Impossible violation (ERROR)
                if min_pos is not None and num_val < min_pos:
                    violation_count += 1
                    issues.append(
                        ValidationIssue(
                            check="range_check_impossible",
                            column=col,
                            severity=IssueSeverity.ERROR,
                            row_index=row_idx,
                            value=num_val,
                            expected=f"Value must be >= {min_pos} {unit}",
                            message=f"Row {row_idx}: {col} value {num_val} {unit} is below scientifically impossible threshold ({min_pos} {unit})"
                        )
                    )
                elif max_pos is not None and num_val > max_pos:
                    violation_count += 1
                    issues.append(
                        ValidationIssue(
                            check="range_check_impossible",
                            column=col,
                            severity=IssueSeverity.ERROR,
                            row_index=row_idx,
                            value=num_val,
                            expected=f"Value must be <= {max_pos} {unit}",
                            message=f"Row {row_idx}: {col} value {num_val} {unit} exceeds scientifically impossible threshold ({max_pos} {unit})"
                        )
                    )
                # 2. Unusual observation (WARNING)
                elif min_warn is not None and num_val < min_warn:
                    issues.append(
                        ValidationIssue(
                            check="range_check_unusual",
                            column=col,
                            severity=IssueSeverity.WARNING,
                            row_index=row_idx,
                            value=num_val,
                            expected=f"Typical range [{min_warn}, {max_warn}] {unit}",
                            message=f"Row {row_idx}: {col} value {num_val} {unit} is unusually low (typical min: {min_warn} {unit})"
                        )
                    )
                elif max_warn is not None and num_val > max_warn:
                    issues.append(
                        ValidationIssue(
                            check="range_check_unusual",
                            column=col,
                            severity=IssueSeverity.WARNING,
                            row_index=row_idx,
                            value=num_val,
                            expected=f"Typical range [{min_warn}, {max_warn}] {unit}",
                            message=f"Row {row_idx}: {col} value {num_val} {unit} is unusually high (typical max: {max_warn} {unit})"
                        )
                    )

        return issues, violation_count


class OutlierDetector:
    """Detects statistical outliers using explainable Interquartile Range (IQR) method."""

    def __init__(self, iqr_multiplier: float = 1.5, min_samples: int = 5):
        self.multiplier = iqr_multiplier
        self.min_samples = min_samples

    def detect(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[ValidationIssue], int]:
        """
        Calculates Q1, Q3, and IQR per numeric column and flags values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR].
        Outliers are flagged with explanatory details, NOT deleted.
        """
        if not records or len(records) < self.min_samples:
            return [], 0

        issues: List[ValidationIssue] = []
        total_outliers = 0

        # Collect numeric values per column
        col_values: Dict[str, List[Tuple[int, float]]] = {}
        for row_idx, row in enumerate(records):
            for col, val in row.items():
                if col in ("latitude", "longitude", "station", "sample", "dataset", "source", "time", "species"):
                    continue  # Skip spatial/temporal/categorical coordinates in statistical outlier test
                if val is not None:
                    try:
                        num_val = float(val)
                        if not math.isnan(num_val) and not math.isinf(num_val):
                            col_values.setdefault(col, []).append((row_idx, num_val))
                    except (ValueError, TypeError):
                        pass

        for col, pairs in col_values.items():
            if len(pairs) < self.min_samples:
                continue

            values_only = sorted([p[1] for p in pairs])
            n = len(values_only)

            # Compute Q1 (25th percentile) and Q3 (75th percentile)
            q1_idx = int(0.25 * n)
            q3_idx = int(0.75 * n)
            q1 = values_only[q1_idx]
            q3 = values_only[q3_idx]
            iqr = q3 - q1

            if iqr <= 0.0:
                continue  # All values identical or very narrow

            lower_bound = q1 - (self.multiplier * iqr)
            upper_bound = q3 + (self.multiplier * iqr)

            for row_idx, val in pairs:
                if val < lower_bound or val > upper_bound:
                    total_outliers += 1
                    issues.append(
                        ValidationIssue(
                            check="statistical_outlier_iqr",
                            column=col,
                            severity=IssueSeverity.WARNING,
                            row_index=row_idx,
                            value=val,
                            expected=f"Within IQR bounds [{round(lower_bound, 3)}, {round(upper_bound, 3)}] (Q1={round(q1, 3)}, Q3={round(q3, 3)}, IQR={round(iqr, 3)})",
                            message=f"Row {row_idx}: {col} value {val} is a statistical outlier beyond {self.multiplier}x IQR bounds"
                        )
                    )

        return issues, total_outliers
