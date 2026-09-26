# Fisheries Catch Prediction V2 — Integration Guide (Phase 14.3 V2)

This guide documents the procedures for integrating the validated **Fisheries Catch Prediction V2** module into the unified **Marine Intelligence Platform**.

---

## 1. Directory Structure of Integration Package

```text
integration_package/
├── model/
│   ├── final_model.joblib          # Serialized production model
│   ├── preprocessing.joblib        # Fitted ColumnTransformer preprocessor
│   ├── feature_schema.json         # Feature definitions and expected schema
│   └── model_metadata.json         # Complete provenance, training, and test metrics
├── inference/
│   ├── predict_v2.py               # Production predictor class & predict_catch_v2()
│   ├── features_v2.py              # Temporal, spatial, sub-basin, and interaction feature extraction
│   ├── pipeline_v2.py              # Preprocessing utilities and metrics
│   └── __init__.py
├── api/
│   └── catch_routes_v2.py          # FastAPI APIRouter ready for mounting
├── requirements.txt                # Minimal runtime dependencies
└── INTEGRATION_GUIDE.md
```

---

## 2. Where to Copy the Model and Code

```bash
# 1. Copy model artifacts
cp -r fisheries_catch_prediction_v2/integration_package/model/ \
      backend/models/fisheries_catch_v2/

# 2. Copy inference scripts
cp -r fisheries_catch_prediction_v2/integration_package/inference/ \
      backend/ml/fisheries_catch_v2/

# 3. Copy API router
cp fisheries_catch_prediction_v2/integration_package/api/catch_routes_v2.py \
   backend/api/routes/fisheries_v2_routes.py
```

---

## 3. How to Call Prediction in Python

```python
from backend.ml.fisheries_catch_v2.predict_v2 import FisheriesCatchPredictorV2

predictor = FisheriesCatchPredictorV2(model_dir="backend/models/fisheries_catch_v2")

sample_operation = {
    "Fleet": "EUESP",
    "Gear": "PS",
    "Effort": 45.0,
    "EffortUnits": "FHOURS",
    "Month": 8,
    "Year": 2024,
    "Latitude": 12.5,
    "Longitude": 62.5
}
prediction = predictor.predict(sample_operation)
print(f"Predicted Catch: {prediction['predicted_catch_mt']} {prediction['unit']}")
```

---

## 4. API Integration into Unified FastAPI Backend

Mount the provided `catch_routes_v2.py` in `backend/main.py`:

```python
from backend.api.routes.fisheries_v2_routes import router as fisheries_v2_router

app.include_router(fisheries_v2_router, prefix="/api/v1")
```

---

## 5. Model Comparison: V1 vs. V2

| Dimension | 14.3 V1 | 14.3 V2 (This Experiment) |
| :--- | :--- | :--- |
| **Model Architectures Compared** | 3 (Baselines, RF, XGBoost) | **6 Models** (V1 Baseline, Improved Raw XGBoost, Improved Log1p XGBoost, CPUE Catch-Rate, CatBoost, Two-Stage Hurdle) |
| **Feature Engineering** | 48 encoded features | **391 encoded features** (Temporal cyclic, Marine Sub-Basin, Macro-Grid, Fleet x Gear, Gear x Season, Location x Season) |
| **Hurdle sMAPE** | 100.04% | **89.61%** (Two-Stage model reduces percentage error on zero-inflated data) |
| **Validation MAE** | 48.33 MT | **48.17 MT (Two-Stage) / 48.24 MT (Improved Raw XGB)** |
| **Sub-basin Error Breakdown** | General | Stratified across Arabian Sea, Somali Basin, Bay of Bengal, Mozambique Channel |
