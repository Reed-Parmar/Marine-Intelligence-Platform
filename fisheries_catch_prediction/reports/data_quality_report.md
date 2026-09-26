# Phase 14.3 — Fisheries Catch Prediction: Data Quality Audit Report

## 1. Executive Summary
This report presents the complete data quality audit of the official **Indian Ocean Tuna Commission (IOTC) / Food and Agriculture Organization (FAO)** Catch and Effort Surface Fisheries Dataset (`IOTC-2024-WPB22-DATA05-CESurface.csv`). The dataset spans **53 calendar years (1970–2022)** across the Indian Ocean and Arabian Sea, comprising **211,288 raw observations** across 54 attributes.

The audit identified critical data quality requirements: whitespace trailing in flag states, spatial coordinate decoding from 7-digit CWP grids, non-positive effort filtering, and strict target leakage elimination. All cleaning rules were applied deterministically and logged in `audit_summary.json`.

---

## 2. Dataset Overview and Dimensions

| Attribute | Raw Value | Cleaned Value |
| :--- | :--- | :--- |
| **Source Authority** | Indian Ocean Tuna Commission (IOTC) / FAO | Same |
| **Observation Unit** | Stratum-level surface fishery catch & effort | Same |
| **Total Rows** | 211,288 | 211,177 |
| **Total Columns** | 54 | 15 (engineered & leak-free) |
| **Temporal Span** | 1970 – 2022 (53 years) | 1970 – 2022 (53 years) |
| **Geographic Coverage** | Indian Ocean & Arabian Sea (-44.5°S to 29.5°N, 20.5°E to 149.5°E) | Same |
| **Exact Duplicate Rows** | 0 | 0 |

---

## 3. Data Cleaning Rules and Transformation Audit

Every cleaning rule applied to the raw data is documented below with detected anomaly, action taken, rationale, and exact record counts:

### Rule 1: Categorical Whitespace Normalization
- **What was detected**: Categorical string fields (`Fleet`, `Gear`, `EffortUnits`) contained trailing and leading whitespace (e.g., `'EUESP  '`, `'PS '`, `'FHOURS  '`).
- **Action taken**: Applied vectorized `.str.strip()` across all categorical variables.
- **Why necessary**: Prevents artificial category fragmentation and ensures exact One-Hot encoding alignment during training and inference.
- **Affected records**: 211,288 records (100% of raw data).

### Rule 2: CWP 7-Digit Spatial Grid Decoding
- **What was detected**: Geographic locations were encoded as 7-digit CWP grid codes (e.g., `5100043` representing 1°x1° at 0°N, 43°E).
- **Action taken**: Implemented vectorized CWP decoder extracting `Latitude` (center), `Longitude` (center), and `SpatialResolution` (degrees: 1.0° or 5.0°).
- **Why necessary**: Machine learning algorithms require continuous decimal spatial coordinates to learn geographic catch distributions and Arabian Sea/Indian Ocean spatial patterns.
- **Affected records**: 211,288 records (2,091 unique grid codes successfully decoded; 0 failed).

### Rule 3: Non-Positive Effort Removal
- **What was detected**: 111 records contained `Effort == 0.0` while having non-zero catch quantities (up to 225 MT).
- **Action taken**: Filtered out all records where `Effort <= 0.0`.
- **Why necessary**: Fishing effort of 0 is unphysical (fish cannot be landed with zero operational effort); these represent corrupt logbook records or missing effort indicators.
- **Affected records**: 111 records (0.0526% of raw dataset). 211,177 records preserved.

### Rule 4: Target Leakage and Reporting Metadata Removal
- **What was detected**: 
  1. `CatchUnits` was missing (`NaN`) if and only if total catch was 0.0 MT, and `'MT'` when catch was positive—acting as a 100% target leak.
  2. 42 individual species catch columns (`YFT-FS`, `BET-LS`, etc.) mathematically sum to the target `TotalCatchMT`.
  3. `QualityCode`, `Source`, `iGrid`, and `MonthEnd` are administrative post-hoc logbook processing tags unavailable before fishing operations.
- **Action taken**: Dropped 48 columns from the modeling dataset.
- **Why necessary**: Absolute leakage prevention. Only operational features available before fishing are retained.
- **Affected records**: 211,177 records.

---

## 4. Target Variable Audit (`TotalCatchMT`)

The target variable is continuous **Total Catch in Metric Tons (MT)** per fishing stratum, representing the total landed catch of all tuna and associated surface species.

### Descriptive Statistics

| Metric | Value |
| :--- | :--- |
| **Count** | 211,177 |
| **Mean** | 75.55 MT |
| **Std Dev** | 198.95 MT |
| **Minimum** | 0.00 MT |
| **25th Percentile (Q1)** | 0.00 MT |
| **Median (Q2)** | 15.00 MT |
| **75th Percentile (Q3)** | 68.26 MT |
| **90th Percentile** | 193.31 MT |
| **95th Percentile** | 340.46 MT |
| **99th Percentile** | 874.57 MT |
| **Maximum** | 8,829.20 MT |
| **Skewness** | 9.742 (heavily right-skewed) |
| **Zero Catch Records** | 73,994 (35.04%) |

### Zero-Catch Distribution Analysis
- Exactly 35.04% of records recorded 0.0 MT of catch despite genuine fishing effort (mean effort: 13.9 hours/days/sets).
- Zero-catch strata are valid fisheries phenomena (unsuccessful search or sets). The model predicts continuous catch bounded below by 0.0 MT.
- Negative catch values: Exactly 0 records (no invalid negative values existed).

---

## 5. Chronological Partition Audit

In accordance with fisheries science protocols, data was split chronologically to test temporal generalization:

| Partition | Time Span | Total Records | Percentage | Zero Catch % | Mean Catch |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 1970 – 2014 (45 yrs) | 155,605 | 73.68% | 41.43% | 72.58 MT |
| **Validation** | 2015 – 2018 (4 yrs) | 27,880 | 13.20% | 22.00% | 77.89 MT |
| **Test** | 2019 – 2022 (4 yrs) | 27,692 | 13.11% | 12.25% | 89.89 MT |
| **Total** | 1970 – 2022 (53 yrs) | 211,177 | 100.00% | 35.04% | 75.55 MT |

The 2019–2022 test set remained strictly held out and untouched until final evaluation.
