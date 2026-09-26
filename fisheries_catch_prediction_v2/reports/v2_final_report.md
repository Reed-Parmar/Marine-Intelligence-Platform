# Phase 14.3 V2 — Fisheries Catch Prediction: Comprehensive Final Report

**Project**: Marine Intelligence Platform — Phase 14.3 V2 Improvement Experiment  
**Status**: COMPLETED, VALIDATED, BENCHMARKED  
**Date**: September 26, 2026  
**Artifact Directory**: `fisheries_catch_prediction_v2/`  

---

## 1. Executive Summary
Phase 14.3 V2 conducted an extensive, controlled improvement experiment comparing **six distinct machine learning architectures** for continuous fisheries catch quantity prediction (in Metric Tons) using the official Indian Ocean Tuna Commission (IOTC) / FAO dataset (1970–2022).

To maintain absolute scientific comparability:
- The existing 14.3 V1 project was kept **completely untouched**.
- The exact same dataset and exact same chronological train/val/test splits were used:
  - **Train**: 1970–2014 (155,605 observations, 73.68%)
  - **Validation**: 2015–2018 (27,880 observations, 13.20%)
  - **Test**: 2019–2022 (27,692 observations, 13.11%)
- Model tuning and selection occurred **strictly on the Validation set**.
- The winning candidate was evaluated **ONCE on the untouched 2019–2022 test set**.

---

## 2. Candidate Models Evaluated on Validation ($N=27,880$)

| Model Candidate | Architecture Description | Val MAE (MT) $\downarrow$ | Val RMSE (MT) $\downarrow$ | Val $R^2$ $\uparrow$ | Val MedAE (MT) $\downarrow$ | Val sMAPE (%) $\downarrow$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Model 1** | **Current XGBoost Baseline (V1 Benchmark)** | **48.36** | **139.76** | **0.6615** | 15.96 | 103.44% |
| **Model 2** | **Improved Raw-Target XGBoost** (with V2 rich interactions) | **48.24** | **139.54** | **0.6625** | 15.72 | 105.04% |
| **Model 3** | **Improved Log1p XGBoost** ($\log(1+y)$ target) | 53.29 | 173.25 | 0.4798 | 13.20 | 122.33% |
| **Model 4** | **Catch-Rate (CPUE) Model** ($\text{CPUE} \times \text{Effort}$) | 60.18 | 372.84 | -1.4094 | 16.65 | 103.94% |
| **Model 5** | **CatBoost Regressor** (ordered boosting on V2 features) | 50.29 | 145.78 | 0.6317 | 18.43 | 107.53% |
| **Model 6** | **Two-Stage Hurdle Model** (Classifier + Positive Regressor)| **48.17** | **140.69** | **0.6569** | **14.88** | **89.61%** |

### Key Scientific Insights from Model Exploration
1. **Direct Catch Modeling vs CPUE Ratios**:
   - Model 4 (CPUE ratio model) proved mathematically unstable ($R^2 = -1.4094$) because low operational effort (e.g. $<2$ hours) creates extreme CPUE outliers that explode when multiplied by vessel duration. Direct catch regression is far more stable.
2. **Raw vs Log1p Transformations**:
   - Model 3 ($\log(1+y)$) reduced median absolute error on small catches but degraded RMSE to 173.25 MT and $R^2$ to 0.4798 due to exponential error scaling on high-tonnage hauls. Raw squared error optimization remains optimal for commercial catch prediction.
3. **The Hurdle Advantage**:
   - Model 6 (Two-Stage Hurdle) achieved the **lowest percentage error (sMAPE: 89.61% vs 103.44%)** and lowest MedAE (14.88 MT), confirming that separating zero-catch searching from positive school sets benefits percentage metrics.
4. **Overall Accuracy Winner**:
   - Model 1 (Baseline) and Model 2 (Improved Raw XGBoost) achieved top-tier validation variance explanation ($R^2 = 0.6615$–$0.6625$) and lowest validation MAE (~48.2–48.3 MT).

---

## 3. Final Test Evaluation (Evaluated ONCE on 2019–2022 Holdout, $N=27,692$)
- **MAE**: **61.95 MT**
- **RMSE**: **164.75 MT**
- **$R^2$**: **0.5898** (59.0% variance explained)
- **Median Absolute Error (MedAE)**: **18.64 MT**
- **Zero-Safe sMAPE**: **100.11%**
- **Mean Bias**: -26.75 MT
- **Mean Actual Catch**: 89.89 MT
- **Mean Predicted Catch**: 63.15 MT
- **Directional Proportions**: 53.57% underprediction, 46.12% overprediction, 0.31% exact

---

## 4. Stratified Error Summary on Test Set

- **By Catch Magnitude**: Catches $\le 100$ MT (80.1% of records) have an MAE of 24.5 MT and MedAE $< 18$ MT. Catches $>300$ MT have an MAE of 419.6 MT due to conditional mean regression.
- **By Marine Region**:
  - **Arabian Sea**: 4,598 records, **MAE = 57.24 MT**, **RMSE = 139.15 MT**, Bias = -41.77 MT.
  - **Western Equatorial (Somali Basin)**: 17,424 records, **MAE = 56.00 MT**, **RMSE = 150.89 MT**, Bias = -40.86 MT.
  - **Eastern Equatorial**: 3,483 records, **MAE = 63.97 MT**, Bias = +43.91 MT.
- **By Gear**:
  - **Offshore Ring Net (`RNOF`)**: **MAE = 9.26 MT**, RMSE = 17.06 MT.
  - **Baitboat (`BB`)**: **MAE = 35.98 MT**, RMSE = 80.34 MT.
  - **Industrial Purse Seine (`PS`)**: **MAE = 58.60 MT**, RMSE = 125.68 MT.
- **By Fleet**:
  - **Maldives (`MDV`)**: **MAE = 37.58 MT**, Bias = -6.06 MT.
  - **France (`EUFRA`)**: **MAE = 45.89 MT**, Bias = -16.52 MT.
  - **Spain (`EUESP`)**: **MAE = 61.51 MT**, Bias = -38.06 MT.
- **By Year**:
  - 2019: **MAE = 57.06 MT**, RMSE = 140.53 MT
  - 2020: **MAE = 53.13 MT**, RMSE = 138.27 MT
  - 2021: **MAE = 67.93 MT**, RMSE = 174.30 MT
  - 2022: **MAE = 71.29 MT**, RMSE = 203.44 MT
- **By Season**:
  - Spring Intermonsoon: **MAE = 56.71 MT**, RMSE = 153.54 MT
  - NE Monsoon: **MAE = 61.27 MT**, RMSE = 181.11 MT
  - SW Monsoon: **MAE = 63.49 MT**, RMSE = 158.31 MT
  - Autumn Intermonsoon: **MAE = 69.25 MT**, RMSE = 169.45 MT

---

## 5. Deployment Benchmarks & API
- **Model Loading Latency**: **634.78 ms**
- **Single Prediction Latency**: **7.77 ms** (Mean), **6.76 ms** (Median), **10.54 ms** (P95)
- **Batch Prediction Throughput**: **5,501.6 records/second** (0.182 ms/record)
- **FastAPI Endpoints**: Fully tested and operational in `fisheries_catch_prediction_v2/api/main.py`:
  - `GET  /health`
  - `GET  /model-info`
  - `POST /predict`
  - `POST /predict/batch`
- **Pytest Suite**: 13/13 tests passing in 2.02 seconds (`tests/test_fisheries_v2.py`).

---

## 6. Integration Recommendation
- **Current Status**: All V2 artifacts and code are persisted cleanly in `fisheries_catch_prediction_v2/`.
- **V1 Protection**: The existing `fisheries_catch_prediction/` remains completely untouched.
- **Platform Integrity**: As strictly instructed, no integration into the unified Marine Intelligence Platform has been performed yet. Both V1 and V2 are ready for integration consideration.
