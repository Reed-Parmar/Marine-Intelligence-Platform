# Phase 14.3 V2 — Fisheries Catch Prediction (Improvement Experiment)

A comprehensive ML improvement experiment evaluating **six distinct machine learning architectures** for predicting continuous fisheries catch quantities (Metric Tons) from operational, spatial, and temporal fisheries parameters across the Indian Ocean and Arabian Sea.

This project is preserved entirely within `fisheries_catch_prediction_v2/`, leaving Phase 14.3 V1 completely untouched.

---

## 1. Directory Structure

```text
fisheries_catch_prediction_v2/
├── data/
│   ├── raw/                       # Exact same IOTC raw dataset files
│   ├── splits/                    # Exact same chronological splits (train.csv, val.csv, test.csv)
│   └── dataset_manifest.json      # Dataset provenance manifest
├── models/
│   ├── model1_v1_baseline/        # Model 1: Current XGBoost Baseline (.joblib)
│   ├── model2_improved_raw_xgb/   # Model 2: Improved Raw-Target XGBoost (.joblib)
│   ├── model3_improved_log1p_xgb/ # Model 3: Improved Log1p XGBoost (.joblib)
│   ├── model4_catch_rate_cpue/    # Model 4: Catch-Rate CPUE Model (.joblib)
│   ├── model5_catboost/           # Model 5: CatBoost Regressor (.joblib & .cbm)
│   ├── model6_two_stage_hurdle/   # Model 6: Two-Stage Hurdle Model (.joblib)
│   └── final_model/               # Production winning model, preprocessor, and metadata
├── src/
│   ├── features_v2.py             # Temporal, sub-basin, macro-grid, and interaction features
│   ├── pipeline_v2.py             # Preprocessing pipeline and metrics
│   ├── train_v2_experiments.py    # 6-model training, validation tuning, test evaluation
│   ├── predict_v2.py              # Single and batch inference engine
│   └── benchmark_v2.py            # Latency, throughput, and memory benchmarking
├── api/
│   └── main.py                    # Standalone FastAPI service (/health, /predict, /model-info)
├── tests/
│   └── test_fisheries_v2.py       # 13 pytest tests covering features, inference, and API
├── reports/
│   ├── data_quality_report.md     # Data audit and partition parameters
│   ├── v2_model_comparison.md     # Full 6-model comparison on validation and holdout test
│   ├── v2_error_analysis.md       # Stratified error analysis by region, fleet, gear, season
│   ├── v2_final_report.md         # Comprehensive project report
│   └── figures/                   # Diagnostic, residual, and validation comparison plots
├── integration_package/           # Self-contained bundle for future platform integration
│   ├── model/                     # Production model, preprocessor, and schema
│   ├── inference/                 # Ready-to-copy inference scripts
│   ├── api/                       # Pluggable FastAPI APIRouter (catch_routes_v2.py)
│   ├── requirements.txt           # Minimal dependencies
│   └── INTEGRATION_GUIDE.md       # Integration instructions
└── README.md
```

---

## 2. Validation Set Comparison Across All 6 Candidate Models ($N=27,880$)

| Model Candidate | Architecture Description | Val MAE (MT) $\downarrow$ | Val RMSE (MT) $\downarrow$ | Val $R^2$ $\uparrow$ | Val MedAE (MT) $\downarrow$ | Val sMAPE (%) $\downarrow$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Model 1** | **Current XGBoost Baseline** | **48.36** | **139.76** | **0.6615** | 15.96 | 103.44% |
| **Model 2** | **Improved Raw-Target XGBoost** | **48.24** | **139.54** | **0.6625** | 15.72 | 105.04% |
| **Model 3** | **Improved Log1p XGBoost** | 53.29 | 173.25 | 0.4798 | 13.20 | 122.33% |
| **Model 4** | **Catch-Rate (CPUE) Model** | 60.18 | 372.84 | -1.4094 | 16.65 | 103.94% |
| **Model 5** | **CatBoost Regressor** | 50.29 | 145.78 | 0.6317 | 18.43 | 107.53% |
| **Model 6** | **Two-Stage Hurdle Model** | **48.17** | **140.69** | **0.6569** | **14.88** | **89.61%** |

---

## 3. Final Test Evaluation (Evaluated ONCE on Untouched 2019–2022 Holdout, $N=27,692$)

- **Test MAE**: **61.95 MT**
- **Test RMSE**: **164.75 MT**
- **Test $R^2$**: **0.5898** (59.0% variance explained)
- **Test MedAE**: **18.64 MT**
- **Test sMAPE**: **100.11%**
- **Test Mean Bias**: -26.75 MT (Mean Actual: 89.89 MT, Mean Predicted: 63.15 MT)

---

## 4. Stratified Error Highlights on Test Set

- **By Region**:
  - **Arabian Sea**: 4,598 records, **MAE = 57.24 MT**, **RMSE = 139.15 MT**
  - **Western Equatorial (Somali Basin)**: 17,424 records, **MAE = 56.00 MT**, **RMSE = 150.89 MT**
  - **Eastern Equatorial**: 3,483 records, **MAE = 63.97 MT**
- **By Season**:
  - Spring Intermonsoon: **MAE = 56.71 MT**, RMSE = 153.54 MT
  - NE Monsoon: **MAE = 61.27 MT**, RMSE = 181.11 MT
  - SW Monsoon: **MAE = 63.49 MT**, RMSE = 158.31 MT
  - Autumn Intermonsoon: **MAE = 69.25 MT**, RMSE = 169.45 MT
- **By Year**:
  - 2019: **MAE = 57.06 MT**, RMSE = 140.53 MT
  - 2020: **MAE = 53.13 MT**, RMSE = 138.27 MT
  - 2021: **MAE = 67.93 MT**, RMSE = 174.30 MT
  - 2022: **MAE = 71.29 MT**, RMSE = 203.44 MT

---

## 5. Quickstart & Usage

### A. Run Experiment Suite
```bash
python fisheries_catch_prediction_v2/src/train_v2_experiments.py
```

### B. Run Automated Pytest Suite
```bash
python -m pytest fisheries_catch_prediction_v2/tests/test_fisheries_v2.py -v
```

### C. Run Performance Benchmarks
```bash
python fisheries_catch_prediction_v2/src/benchmark_v2.py
```

### D. Start Standalone FastAPI Service
```bash
uvicorn fisheries_catch_prediction_v2.api.main:app --port 8002 --reload
```
