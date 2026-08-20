# Data Quality & Standardisation Engine (Phase 4)

## 1. Overview

The **Data Quality & Standardisation Engine** turns raw, heterogeneous marine scientific records (from CSV, TXT, Excel, JSON, CTD) into standardized, validated, quality-scored research datasets ready for database persistence, spatial/temporal fusion, and scientific analysis.

```text
Incoming Parsed Records (from Phase 3 Ingestion)
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│            Phase 4: Quality & Standardisation          │
├────────────────────────────────────────────────────────┤
│ 1. Schema Normalisation (Column alias mapping)         │
│ 2. Scientific Unit Conversion (Non-destructive)        │
│ 3. Missing Value Analysis (null, empty, -999 markers)  │
│ 4. Duplicate Detection (Exact rows & logical keys)     │
│ 5. Coordinate & Spatial Validation ([-90,90], PostGIS) │
│ 6. Timestamp Standardisation (ISO-8601 UTC)            │
│ 7. Scientific Range Checks (Impossible vs Unusual)    │
│ 8. Statistical Outlier Detection (1.5x IQR)            │
│ 9. Deterministic Quality Scoring (0 - 100)             │
│ 10. Provenance & Validation Notes Generation           │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
DatasetQualityResult (Standardised Records + Quality Score + Issues + Provenance)
```

---

## 2. Standard Internal Representation (Canonical Schema)

Phase 4 maps varied incoming column headers to canonical platform attributes:

### Core Platform Fields
| Canonical Field | Description | Supported Input Aliases |
| :--- | :--- | :--- |
| `latitude` | Decimal degrees [-90.0, 90.0] | `lat`, `latitude`, `lat_dd`, `lat_deg`, `decimal_latitude`, `dec_lat`, `y`, `station_lat` |
| `longitude` | Decimal degrees [-180.0, 180.0] | `lon`, `long`, `longitude`, `lon_dd`, `lon_deg`, `decimal_longitude`, `dec_lon`, `x` |
| `time` | ISO-8601 UTC timestamp | `time`, `timestamp`, `datetime`, `date_time`, `date`, `sampling_date`, `time_utc`, `event_date` |
| `depth` | Water depth in meters (m) | `depth`, `depth_m`, `depth_meters`, `z`, `water_depth`, `sample_depth`, `sounding` |
| `station` | Sampling station/site ID | `station`, `station_id`, `station_name`, `site`, `site_id`, `sampling_station`, `stn_no` |
| `sample` | Sample or specimen code | `sample`, `sample_id`, `sample_code`, `specimen_id`, `event_id` |
| `species` | Scientific name / taxon | `species`, `scientific_name`, `taxon`, `taxa`, `species_name`, `organism_name` |
| `dataset` | Dataset or cruise ID | `dataset`, `dataset_id`, `dataset_name`, `cruise`, `cruise_id`, `survey_id` |
| `source` | Provider or vessel name | `source`, `data_source`, `institution`, `provider`, `vessel`, `vessel_name` |

### Oceanographic Measurements
| Canonical Field | Standard Unit | Input Aliases |
| :--- | :--- | :--- |
| `temperature` | °C (Celsius) | `temperature`, `temp`, `temp_c`, `water_temp`, `sst`, `sea_water_temperature`, `t_degc` |
| `salinity` | PSU (Practical Salinity Units) | `salinity`, `sal`, `sal_psu`, `practical_salinity`, `sea_water_salinity`, `s_psu` |
| `dissolved_oxygen` | mg/L | `dissolved_oxygen`, `do`, `d_o`, `oxygen`, `o2`, `do_mg_l`, `oxygen_concentration` |
| `chlorophyll` | mg/m³ | `chlorophyll`, `chlorophyll_a`, `chl`, `chla`, `chl_a`, `fluorescence`, `chl_mg_m3` |
| `ph` | pH units | `ph`, `sea_water_ph`, `ph_total`, `water_ph` |
| `pressure` | dbar (decibars) | `pressure`, `press`, `dbar`, `pressure_dbar`, `sea_water_pressure` |
| `turbidity` | NTU | `turbidity`, `turb`, `ntu`, `turbidity_ntu` |
| `conductivity` | mS/cm | `conductivity`, `cond`, `c_ms_cm`, `electrical_conductivity` |

### Fisheries Measurements
| Canonical Field | Standard Unit | Input Aliases |
| :--- | :--- | :--- |
| `catch_weight_kg` | kg | `catch_weight`, `catch_weight_kg`, `catch_kg`, `weight_kg`, `total_catch`, `landings_kg` |
| `effort_hours` | hours | `effort_hours`, `fishing_effort`, `effort_hr`, `hours_fished`, `duration_hours` |
| `gear_type` | text | `gear_type`, `gear`, `fishing_gear`, `gear_code`, `method` |
| `fishing_zone` | text | `fishing_zone`, `zone`, `fao_area`, `eez_zone`, `grid`, `area_code` |
| `species_common_name`| text | `species_common_name`, `common_name`, `local_name`, `vernacular_name` |

---

## 3. Scientific Unit Conversions & Timezone Policy

The unit converter normalizes measurements into standardized scientific units and logs every conversion to the provenance audit log:

- **Timestamp & Timezone Policy**:
  - **Explicit Timezone Present**: When timestamps contain explicit timezone indicators (e.g., `Z`, `UTC`, `GMT`, `+05:30`, `-04:00`), they are normalized to standard ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
  - **Naive / Timezone-less**: When timestamps contain no timezone information (e.g. `15/03/2026 08:30` or `2026-03-15`), the representation is standardized without appending `'Z'` or assuming UTC. A validation note (`timezone_status = "unknown"`) is recorded. The system never silently assumes IST, UTC, vessel time, or local time.
- **Temperature**:
  - Fahrenheit (°F) → Celsius (°C): $(°F - 32) \times \frac{5}{9}$
  - Kelvin (K) → Celsius (°C): $K - 273.15$
- **Depth**:
  - Feet (ft) → Meters (m): $ft \times 0.3048$
  - Fathoms → Meters (m): $fathom \times 1.8288$
  - Kilometers (km) → Meters (m): $km \times 1000$
- **Dissolved Oxygen**:
  - **Rule**: Conversion is **only applied when the source unit is explicitly provided** via `unit_hints`. The system never infers or guesses that a generic `DO` column is in `mL/L`.
  - Milliliters per Liter (mL/L) → mg/L: $mL/L \times 1.42903$
  - *Scientific Assumption Note*: The $1.42903$ factor is an approximate/simple conversion assumption based on oxygen density at Standard Temperature and Pressure (STP, $0^\circ\text{C}, 1\text{ atm}$). Rigorous in-situ marine density calculations require seawater salinity and temperature equations of state (UNESCO 1983 / TEOS-10).
  - Parts per Million (ppm) → mg/L: $ppm \times 1.0$
- **Pressure**:
  - Bar → Decibar (dbar): $bar \times 10.0$
  - PSI → Decibar (dbar): $psi \times 0.689476$
  - Atmosphere (atm) → Decibar (dbar): $atm \times 10.1325$
- **Coordinates**:
  - Degrees Minutes Seconds (DMS) / Degrees Decimal Minutes (DDM) $\rightarrow$ Decimal Degrees (DD).
  - Example: `10° 15' 30" N` $\rightarrow$ `10.258333`

---

## 4. Scientific Range Rules & Assumptions

Documented oceanographic validation bounds (referenced from IOC/UNESCO QARTOD & World Ocean Database):

| Parameter | Unit | Scientifically Impossible Bound (ERROR) | Typical Marine Range (WARNING) | Scientific Assumption |
| :--- | :--- | :--- | :--- | :--- |
| **Temperature** | °C | `[-2.5, 42.0]` | `[0.0, 35.0]` | Seawater freezes at ~ -2°C at 35 PSU; surface pools reach ~40°C. |
| **Salinity** | PSU | `[0.0, 46.0]` | `[10.0, 42.0]` | Estuaries reach 0 PSU; Red Sea / Persian Gulf lagoon extremes ~45 PSU. |
| **Dissolved Oxygen** | mg/L | `[0.0, 25.0]` | `[0.5, 15.0]` | 0 mg/L in anoxic basins; up to ~22 mg/L in intense phytoplankton blooms. |
| **Depth** | m | `[0.0, 11500.0]` | `[0.0, 6500.0]` | Negative depth is above sea surface; Challenger Deep max is ~10,928 m. |
| **Chlorophyll-a** | mg/m³ | `[0.0, 150.0]` | `[0.01, 50.0]` | Oligotrophic open ocean ~0.01; red tide blooms reach >100 mg/m³. |
| **pH** | pH | `[6.0, 9.5]` | `[7.3, 8.6]` | Normal open ocean surface water is 8.1 - 8.3. |
| **Pressure** | dbar | `[0.0, 13000.0]` | `[0.0, 7000.0]` | Hydrostatic pressure increases ~1 dbar per meter depth. |
| **Catch Weight** | kg | `[0.0, 500000.0]` | `[0.0, 50000.0]` | Commercial purse seine / trawl catch per haul. |
| **Effort Hours** | hours | `[0.0, 720.0]` | `[0.1, 72.0]` | Single sampling or survey haul duration. |

---

## 5. Outlier Detection Method

- **Algorithm**: Statistical Interquartile Range (IQR).
- **Rule**: A value $x$ is flagged as an outlier if $x < Q1 - 1.5 \times IQR$ or $x > Q3 + 1.5 \times IQR$.
- **Behavior**: Outliers are **flagged with descriptive context**, never automatically removed or mutated.

---

## 6. Deterministic Quality Scoring (0 - 100)

> **Important Scientific Scope**:
> The Quality Score is an **internal data quality control (QC) indicator** based on the platform's predefined validation criteria (completeness, spatial bounds, temporal validity, range checks, duplicates, and schema consistency).
> It is **NOT** a measurement of absolute scientific accuracy or ground truth (e.g. a dataset scored 87/100 represents *"Quality Score: 87/100 based on the platform's predefined QC criteria"*, not *"87% scientifically accurate"*).

The dataset quality score is computed deterministically from 100 points:

$$\text{Quality Score} = \max(0, 100 - \sum \text{Deductions})$$

### Deductions:
1. **Spatial Integrity (Coordinates)**: Max $-25\text{ pts}$ ($\min(25, \text{coord\_error\_ratio} \times 40)$).
2. **Temporal Integrity (Timestamps)**: Max $-20\text{ pts}$ ($\min(20, \text{time\_error\_ratio} \times 35)$).
3. **Scientific Validity (Range Checks)**: Max $-15\text{ pts}$ ($\min(15, \text{range\_error\_ratio} \times 30)$).
4. **Data Completeness (Missing Values)**: Max $-15\text{ pts}$ ($\min(15, \frac{\text{missing\_pct}}{40} \times 15)$).
5. **Record Uniqueness (Duplicates)**: Max $-10\text{ pts}$ ($\min(10, \frac{\text{duplicate\_pct}}{25} \times 10)$).
6. **Schema Compliance (Unmapped Fields)**: Max $-10\text{ pts}$ ($\min(10, \text{unmapped\_count} \times 2)$).
7. **Statistical Consistency (Outliers)**: Max $-5\text{ pts}$ ($\min(5, \text{outlier\_ratio} \times 5)$).

### Quality Status Thresholds:
- **`PASSED`**: Quality Score $\ge 85.0$ and $0$ critical errors.
- **`FLAGGED`**: Quality Score $60.0 - 84.9$ or non-fatal warnings present.
- **`FAILED`**: Quality Score $< 60.0$ or critical spatial/temporal errors affecting $> 25\%$ of records.

---

## 7. Phase 3 Ingestion Integration Interface

Phase 3 connects to Phase 4 using the `QualityPipeline` class:

```python
from data_pipeline.pipeline import QualityPipeline

# 1. Initialize pipeline with optional domain configurations
pipeline = QualityPipeline(
    unit_hints={"temperature": "fahrenheit", "depth": "feet"},
    custom_column_mapping={"stn_name": "station"}
)

# 2. Process parsed records from Phase 3
raw_records = [
    {"Date": "2026-03-15", "Lat": 9.93, "Lon": 76.26, "Depth": 100, "Temp": 86.0, "DO": 5.8},
    {"Date": "2026-03-15", "Lat": 9.94, "Lon": 76.27, "Depth": 150, "Temp": "-999", "DO": 5.6}
]

dataset_metadata = {
    "id": "d1a2b3c4-0000-0000-0000-000000000001",
    "domain_type": "oceanography"
}

result = pipeline.process(raw_records, dataset_metadata=dataset_metadata)

# 3. Access clean standardized records & quality indicators
print("Quality Score:", result.quality_score)         # e.g., 94.5
print("Quality Status:", result.quality_status.value)  # e.g., 'passed'
print("Validation Notes:\n", result.validation_notes)
print("Standardized Rows:", len(result.standardised_records))

# 4. Save directly to Supabase / PostgreSQL datasets table
postgres_payload = result.to_postgres_dataset_update()
# postgres_payload contains:
# - quality_score (NUMERIC)
# - quality_status (TEXT: 'passed' | 'flagged' | 'failed')
# - validation_notes (TEXT)
# - provenance_metadata (JSONB)
```

---

## 8. Provenance & Audit Model

Phase 4 preserves full lineage without destructive mutations. The `provenance` metadata object stored in `public.datasets.provenance_metadata` contains:

```json
{
  "pipeline_name": "CMLRE Data Quality & Standardisation Engine",
  "pipeline_version": "phase-4-v1.0.0",
  "processed_at": "2026-08-20T13:07:00Z",
  "dataset_id": "d1a2b3c4-0000-0000-0000-000000000001",
  "domain_type": "oceanography",
  "input_record_count": 500,
  "quality_status": "passed",
  "quality_score": 96.8,
  "transformation_summary": {
    "total_transformations": 12,
    "unmapped_columns": ["turbidity_manual_reading"],
    "sample_transformations": [
      {
        "column": "temperature",
        "row_index": 0,
        "original_value": 86.0,
        "transformed_value": 30.0,
        "rule": "Converted 86.0°F to 30.0°C",
        "timestamp": "2026-08-20T13:07:00Z"
      },
      {
        "column": "time",
        "row_index": 0,
        "original_value": "15/03/2026 08:30",
        "transformed_value": "2026-03-15T08:30:00Z",
        "rule": "Standardized timestamp to ISO-8601 UTC",
        "timestamp": "2026-08-20T13:07:00Z"
      }
    ]
  }
}
```
