# Phase 14.3 — Fisheries Catch Prediction (Standalone ML Project)

A production-grade, standalone machine learning system for predicting continuous fisheries catch quantities (Metric Tons) from operational, spatial, and temporal fisheries parameters across the Indian Ocean and Arabian Sea.

This project forms **Component 3** of the larger **Marine Intelligence Platform**, developed and validated completely independently before future platform integration.

---

## 1. Project Directory Structure

```text
fisheries_catch_prediction/
├── data/
│   ├── raw/                       # Official IOTC Catch & Effort zip and CSV
│   ├── processed/                 # Cleaned dataset (fisheries_catch_clean.csv) & audit_summary.json
│   ├── splits/                    # Chronological splits (train.csv, val.csv, test.csv)
│   └── dataset_manifest.json      # Complete dataset provenance manifest
├── models/
│   ├── baseline/                  # Mean and Median baseline models (.joblib)
│   ├── random_forest/             # Trained Random Forest Regressor (.joblib)
│   ├── xgboost/                   # Initial XGBoost Regressor (.json & .joblib)
│   └── final_model/               # Tuned production XGBoost model, preprocessor, schemas & metadata
├── src/
│   ├── data_processing.py         # CWP grid decoding, cleaning, and chronological splitting
│   ├── pipeline.py                # Preprocessor, feature engineering, and metrics
│   ├── train_models.py            # Training, validation tuning, test evaluation, and SHAP
│   ├── predict.py                 # Clean single and batch inference API
│   └── benchmark.py               # Latency, throughput, and memory benchmarking
├── api/
│   └── main.py                    # Standalone FastAPI service (/health, /predict, /model-info)
├── tests/
│   └── test_fisheries_model.py    # 18 pytest tests covering pipeline, inference, and API
├── reports/
│   ├── data_quality_report.md     # Full data quality audit and cleaning rules
│   ├── model_comparison.md        # Baselines, Random Forest, and XGBoost comparative analysis
│   ├── error_analysis.md          # Stratified error analysis by fleet, gear, month, catch tier
│   ├── final_report.md            # Comprehensive 21-section project report
│   └── figures/                   # Diagnostic, residual, feature importance, and SHAP plots
├── integration_package/           # Self-contained bundle for future platform integration
│   ├── model/                     # Serialized production model, preprocessor, and metadata
│   ├── inference/                 # Ready-to-copy inference scripts
│   ├── api/                       # Plug-and-play APIRouter (catch_routes.py)
│   ├── requirements.txt           # Minimal runtime dependencies
│   └── INTEGRATION_GUIDE.md       # Integration instructions for FastAPI & React
└── README.md
```

---

## 2. Key Performance Metrics

Evaluated on the **strictly held-out 2019–2022 test set (27,692 observations)**:

| Metric | Mean Baseline | Random Forest | XGBoost (Tuned Final) |
| :--- | :--- | :--- | :--- |
| **MAE** | 96.86 MT | 59.31 MT | **61.68 MT** (36.3% error reduction) |
| **RMSE** | 257.79 MT | 160.95 MT | **164.47 MT** (93.3 MT reduction) |
| **$R^2$** | -0.0045 | 0.6084 | **0.5911** (59.1% variance explained) |
| **Median Abs Error** | 62.23 MT | 18.92 MT | **18.43 MT** |
| **sMAPE** | 117.17% | 95.61% | **100.04%** |
| **Model Size** | <1 KB | 187.1 MB | **3.2 MB** (58x smaller than RF) |
| **Single Latency** | <1 ms | 38.5 ms | **6.14 ms** |
| **Throughput** | N/A | 310 records/s | **5,346 records/s** |

---

## 3. Quickstart & Usage

### A. Run Data Processing & Quality Audit
```bash
python fisheries_catch_prediction/src/data_processing.py
```

### B. Run Model Training & Evaluation Suite
```bash
python fisheries_catch_prediction/src/train_models.py
```

### C. Run Performance Benchmarks
```bash
python fisheries_catch_prediction/src/benchmark.py
```

### D. Run Automated Test Suite
```bash
pytest fisheries_catch_prediction/tests/test_fisheries_model.py -v
```

### E. Start Standalone FastAPI Service
```bash
python fisheries_catch_prediction/api/main.py
```
Or with Uvicorn:
```bash
uvicorn fisheries_catch_prediction.api.main:app --port 8001 --reload
```

---

## 4. API Endpoints

- **`GET /health`**: Health check, model status, and uptime.
- **`GET /model-info`**: Model metadata, feature schema, and evaluation metrics.
- **`POST /predict`**: Single record prediction in Metric Tons.
- **`POST /predict/batch`**: High-throughput batch prediction.

Example prediction request:
```json
POST /predict
{
  "Fleet": "EUESP",
  "Gear": "PS",
  "Effort": 45.0,
  "EffortUnits": "FHOURS",
  "Month": 8,
  "Year": 2024,
  "Latitude": 2.5,
  "Longitude": 55.5
}
```

Response:
```json
{
  "predicted_catch": 108.83,
  "unit": "Metric Tons (MT)",
  "model": "XGBoost Regressor (Tuned)",
  "model_version": "1.0.0",
  "input_summary": {
    "fleet": "EUESP",
    "gear": "PS",
    "effort": 45.0,
    "effort_units": "FHOURS",
    "month": 8,
    "year": 2024,
    "latitude": 2.5,
    "longitude": 55.5,
    "season": "SW_Monsoon"
  }
}
```

---

## 5. Future Integration

When integration into the main Marine Intelligence Platform is scheduled:
Consult [INTEGRATION_GUIDE.md](file:///c:/Users/Office%20Pc/Downloads/Marine-Intelligence-Platform-moksh-add-frontend%20%281%29/Marine-Intelligence-Platform-moksh-add-frontend/fisheries_catch_prediction/integration_package/INTEGRATION_GUIDE.md) in the `integration_package/` folder.  
**DO NOT** integrate into the main platform until requested.
