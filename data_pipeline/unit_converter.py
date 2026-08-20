"""
Scientific unit converter for Phase 4.
Performs deterministic, scientifically documented unit transformations and records provenance.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple
from data_pipeline.models import ValidationIssue, IssueSeverity, TransformationRecord


class UnitConverter:
    """
    Handles scientific unit standardization across marine variables.
    
    Standard target units:
    - Temperature: Celsius (°C)
    - Depth: Meters (m)
    - Dissolved Oxygen: Milligrams per Liter (mg/L)
    - Pressure: Decibars (dbar)
    - Salinity: Practical Salinity Units (PSU / unitless)
    - Coordinates: Decimal Degrees (DD)
    """

    def __init__(self, unit_hints: Optional[Dict[str, str]] = None):
        """
        unit_hints: Optional mapping of field_name -> source_unit.
        Example: {'temperature': 'fahrenheit', 'depth': 'feet'}
        """
        self.unit_hints: Dict[str, str] = {k.lower(): v.lower() for k, v in (unit_hints or {}).items()}

    @staticmethod
    def parse_dms_coordinate(coord_str: str) -> Optional[float]:
        """
        Parses Degrees Minutes Seconds (DMS) or Degrees Decimal Minutes (DDM) to decimal degrees.
        Examples:
            '10° 15\' 30" N' -> 10.258333
            '76° 12.5\' E' -> 76.208333
            '10 15 30 S' -> -10.258333
        """
        if not isinstance(coord_str, str):
            return None
            
        s = coord_str.strip().upper()
        if not s:
            return None

        # Detect direction hemisphere
        hemisphere = None
        if s.endswith(('N', 'S', 'E', 'W')):
            hemisphere = s[-1]
            s = s[:-1].strip()
        elif s.startswith(('N', 'S', 'E', 'W')):
            hemisphere = s[0]
            s = s[1:].strip()

        # Extract numeric components using regex
        parts = re.findall(r"[-+]?\d*\.?\d+", s)
        if not parts:
            return None

        try:
            if len(parts) == 1:
                val = float(parts[0])
            elif len(parts) == 2:  # Degrees and decimal minutes (DDM)
                deg = float(parts[0])
                mins = float(parts[1])
                val = deg + (mins / 60.0)
            elif len(parts) >= 3:  # Degrees, minutes, seconds (DMS)
                deg = float(parts[0])
                mins = float(parts[1])
                secs = float(parts[2])
                val = deg + (mins / 60.0) + (secs / 3600.0)
            else:
                return None

            if hemisphere in ('S', 'W'):
                val = -abs(val)
            elif hemisphere in ('N', 'E'):
                val = abs(val)

            return round(val, 6)
        except (ValueError, TypeError):
            return None

    def convert_temperature(self, value: float, source_unit: str) -> Tuple[float, str]:
        """Converts temperature to Celsius (°C)."""
        u = source_unit.lower()
        if u in ("fahrenheit", "f", "degf", "deg_f", "°f"):
            c = (value - 32.0) * (5.0 / 9.0)
            return round(c, 3), f"Converted {value}°F to {round(c, 3)}°C"
        elif u in ("kelvin", "k", "degk"):
            c = value - 273.15
            return round(c, 3), f"Converted {value}K to {round(c, 3)}°C"
        return value, "No conversion needed (already Celsius)"

    def convert_depth(self, value: float, source_unit: str) -> Tuple[float, str]:
        """Converts depth to meters (m)."""
        u = source_unit.lower()
        if u in ("feet", "ft", "foot"):
            m = value * 0.3048
            return round(m, 2), f"Converted {value} ft to {round(m, 2)} m"
        elif u in ("fathoms", "fathom", "fath"):
            m = value * 1.8288
            return round(m, 2), f"Converted {value} fathoms to {round(m, 2)} m"
        elif u in ("kilometers", "km"):
            m = value * 1000.0
            return round(m, 2), f"Converted {value} km to {round(m, 2)} m"
        elif u in ("centimeters", "cm"):
            m = value * 0.01
            return round(m, 2), f"Converted {value} cm to {round(m, 2)} m"
        return value, "No conversion needed (already meters)"

    def convert_dissolved_oxygen(self, value: float, source_unit: str) -> Tuple[float, str]:
        """
        Converts dissolved oxygen to standard mg/L ONLY when source unit is explicitly provided.
        
        Scientific note: The 1.42903 factor is an approximate/simple conversion assumption at
        Standard Temperature and Pressure (STP, 0°C, 1 atm). Rigorous marine in-situ conversion
        requires potential density and salinity equations of state (UNESCO 1983 / TEOS-10).
        1 ppm ≈ 1 mg/L for dilute aqueous solutions.
        """
        u = source_unit.lower()
        if u in ("ml/l", "ml_l", "ml_per_l", "milliliters_per_liter"):
            mgl = value * 1.42903
            return round(mgl, 3), f"Converted {value} mL/L to {round(mgl, 3)} mg/L (approximate STP factor: 1.42903)"
        elif u in ("ppm", "parts_per_million"):
            mgl = value * 1.0
            return round(mgl, 3), f"Converted {value} ppm to {round(mgl, 3)} mg/L (factor: 1.0)"
        return value, "No conversion needed (already mg/L or unit unknown)"

    def convert_pressure(self, value: float, source_unit: str) -> Tuple[float, str]:
        """Converts pressure to decibars (dbar)."""
        u = source_unit.lower()
        if u in ("bar", "bars"):
            dbar = value * 10.0
            return round(dbar, 2), f"Converted {value} bar to {round(dbar, 2)} dbar"
        elif u in ("psi", "lb_sq_in"):
            dbar = value * 0.689476
            return round(dbar, 2), f"Converted {value} psi to {round(dbar, 2)} dbar"
        elif u in ("atm", "atmosphere"):
            dbar = value * 10.1325
            return round(dbar, 2), f"Converted {value} atm to {round(dbar, 2)} dbar"
        elif u in ("pa", "pascal"):
            dbar = value / 10000.0
            return round(dbar, 2), f"Converted {value} Pa to {round(dbar, 2)} dbar"
        elif u in ("kpa", "kilopascal"):
            dbar = value / 10.0
            return round(dbar, 2), f"Converted {value} kPa to {round(dbar, 2)} dbar"
        return value, "No conversion needed (already dbar)"

    def standardize_record(
        self,
        record: Dict[str, Any],
        row_idx: int
    ) -> Tuple[Dict[str, Any], List[ValidationIssue], List[TransformationRecord]]:
        """Standardizes numeric values and units for a single record."""
        std_row = dict(record)
        issues: List[ValidationIssue] = []
        transformations: List[TransformationRecord] = []

        for field_name, value in record.items():
            if value is None or value == "":
                continue

            # Check coordinate string conversions (e.g. DMS string format to decimal degrees)
            if field_name in ("latitude", "longitude") and isinstance(value, str):
                parsed_coord = self.parse_dms_coordinate(value)
                if parsed_coord is not None:
                    std_row[field_name] = parsed_coord
                    transformations.append(
                        TransformationRecord(
                            column=field_name,
                            row_index=row_idx,
                            original_value=value,
                            transformed_value=parsed_coord,
                            rule=f"Coordinate DMS/DDM string converted to decimal degrees: '{value}' -> {parsed_coord}"
                        )
                    )

            # Check if there is an explicit unit hint for this field
            unit_hint = self.unit_hints.get(field_name.lower())
            if not unit_hint:
                continue

            try:
                num_val = float(value)
            except (ValueError, TypeError):
                continue

            # Temperature conversions
            if field_name == "temperature" and unit_hint not in ("c", "celsius", "degc"):
                new_val, rule_desc = self.convert_temperature(num_val, unit_hint)
                std_row[field_name] = new_val
                transformations.append(
                    TransformationRecord(
                        column=field_name,
                        row_index=row_idx,
                        original_value=value,
                        transformed_value=new_val,
                        rule=rule_desc
                    )
                )

            # Depth conversions
            elif field_name == "depth" and unit_hint not in ("m", "meter", "meters"):
                new_val, rule_desc = self.convert_depth(num_val, unit_hint)
                std_row[field_name] = new_val
                transformations.append(
                    TransformationRecord(
                        column=field_name,
                        row_index=row_idx,
                        original_value=value,
                        transformed_value=new_val,
                        rule=rule_desc
                    )
                )

            # Dissolved oxygen conversions
            elif field_name == "dissolved_oxygen" and unit_hint not in ("mg/l", "mgl", "mg_l"):
                new_val, rule_desc = self.convert_dissolved_oxygen(num_val, unit_hint)
                std_row[field_name] = new_val
                transformations.append(
                    TransformationRecord(
                        column=field_name,
                        row_index=row_idx,
                        original_value=value,
                        transformed_value=new_val,
                        rule=rule_desc
                    )
                )

            # Pressure conversions
            elif field_name == "pressure" and unit_hint not in ("dbar", "decibar", "decibars"):
                new_val, rule_desc = self.convert_pressure(num_val, unit_hint)
                std_row[field_name] = new_val
                transformations.append(
                    TransformationRecord(
                        column=field_name,
                        row_index=row_idx,
                        original_value=value,
                        transformed_value=new_val,
                        rule=rule_desc
                    )
                )

        return std_row, issues, transformations
