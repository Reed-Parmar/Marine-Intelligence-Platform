# Phase 14.3 V2 — Fisheries Catch Prediction: Data Quality & Partition Report

## 1. Executive Summary
This report documents the exact data quality audit, cleaning verification, and chronological partition parameters for **Phase 14.3 V2 — Fisheries Catch Prediction Improvement Experiment**.

As strictly required, **V2 utilized the exact same real dataset and the exact same chronological split** as V1 to maintain strict scientific comparability:
- Dataset: Official IOTC Surface Fisheries Catch and Effort Dataset (`IOTC-2024-WPB22-DATA05-CESurface.csv`, 1970–2022).
- Cleaned observations: 211,177 records.
- Chronological partitions:
  - **Train**: 1970–2014 (155,605 records, 73.68%)
  - **Validation**: 2015–2018 (27,880 records, 13.20%)
  - **Test**: 2019–2022 (27,692 records, 13.11%)
- The final test set (2019–2022) remained **strictly untouched** during all tuning and model selection decisions.

---

## 2. Target Variable Verification
- **Target Column**: `TotalCatchMT` (Metric Tons)
- Continuous variable representing the total landed catch of all tuna species (*Thunnus albacares*, *Katsuwonus pelamis*, *Thunnus obesus*, *Thunnus alalunga*) and associated pelagic species.
- Range: `[0.00, 8,829.20] MT`. Mean: `75.55 MT`, Median: `15.00 MT`.
- Skewness: `9.742` (heavily right-skewed).
- Zero-catch records: 73,994 (35.04% of dataset).

---

## 3. Data Leakage Enforcement
All leakage rules established in V1 were strictly preserved:
1. `CatchUnits` was eliminated (previously 100% collinear with positive catch).
2. All 42 individual species catch breakdowns (`YFT-FS`, `SKJ-LS`, etc.) were excluded because their direct sum constitutes the target variable.
3. Post-hoc logbook reporting tags (`QualityCode`, `Source`, `iGrid`) were excluded to reflect only operational parameters available prior to fishing.
