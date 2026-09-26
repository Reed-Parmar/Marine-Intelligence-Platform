# Fisheries Catch Prediction — Integration Guide (Phase 14.3)

This guide documents the procedures for integrating the validated, standalone **Fisheries Catch Prediction** module into the unified **Marine Intelligence Platform** (FastAPI backend and React frontend).

---

## 1. Where to Copy the Model and Code

When the time arrives to merge this component into the main platform:

```bash
# 1. Copy model artifacts
cp -r fisheries_catch_prediction/integration_package/model/ \
      backend/models/fisheries_catch/

# 2. Copy inference scripts
cp -r fisheries_catch_prediction/integration_package/inference/ \
      backend/ml/fisheries_catch/

# 3. Copy API router
cp fisheries_catch_prediction/integration_package/api/catch_routes.py \
   backend/api/routes/fisheries_routes.py
```

---

## 2. Required Dependencies

Add the following packages to `backend/requirements.txt`:

```text
xgboost>=2.1.0
scikit-learn>=1.5.0
pandas>=2.0.0
numpy>=1.26.0
joblib>=1.3.0
```

---

## 3. How to Load the Model Programmatically

```python
from backend.ml.fisheries_catch.predict import FisheriesCatchPredictor

# Initialize predictor (loads final_model.joblib, preprocessing.joblib, and metadata)
predictor = FisheriesCatchPredictor(model_dir="backend/models/fisheries_catch")
```

---

## 4. How to Call Prediction

### Python Direct Call
```python
# Single prediction
sample_operation = {
    "Fleet": "EUESP",
    "Gear": "PS",
    "Effort": 45.0,
    "EffortUnits": "FHOURS",
    "Month": 8,
    "Year": 2024,
    "Latitude": 2.5,
    "Longitude": 55.5
}
prediction = predictor.predict(sample_operation)
print(f"Predicted Catch: {prediction['predicted_catch_mt']} {prediction['unit']}")

# Batch prediction
operations_batch = [sample_operation, { ... }]
batch_predictions = predictor.predict_batch(operations_batch)
```

---

## 5. Expected Input Schema

| Field Name | Type | Range / Options | Description |
| :--- | :--- | :--- | :--- |
| `Fleet` | `str` | `EUESP`, `EUFRA`, `SYC`, `MDV`, `JPN`, etc. | Flag state / vessel country |
| `Gear` | `str` | `PS` (Purse Seine), `BB` (Baitboat), `RNOF` | Fishing gear type |
| `Effort` | `float` | $\ge 0.0$ | Magnitude of fishing effort expended |
| `EffortUnits`| `str` | `FHOURS`, `FDAYS`, `SETS`, `TRIPS` | Unit of measurement for effort |
| `Month` | `int` | `1` to `12` | Month of fishing activity |
| `Year` | `int` | e.g. `2024` | Calendar year |
| `Latitude` | `float` | `-90.0` to `+90.0` | Coordinate in decimal degrees |
| `Longitude`| `float` | `-180.0` to `+180.0` | Coordinate in decimal degrees |
| `SpatialResolution` | `float` | Optional (default: `1.0`) | Resolution of grid cell (degrees) |

---

## 6. Expected Output Schema

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

## 7. Unified Backend Integration (FastAPI)

Mount the provided `catch_routes.py` in `backend/main.py`:

```python
from backend.api.routes.fisheries_routes import router as fisheries_router

app.include_router(fisheries_router, prefix="/api/v1")
```

This instantly exposes:
- `GET  /api/v1/fisheries/health`
- `GET  /api/v1/fisheries/model-info`
- `POST /api/v1/fisheries/predict`
- `POST /api/v1/fisheries/predict/batch`

---

## 8. Frontend Integration Requirements (React)

1. **Input Form**:
   - Vessel Fleet selector (`EUESP`, `EUFRA`, `SYC`, `MDV`, `JPN`, etc.).
   - Fishing Gear selector (`PS`, `BB`, `RNOF`, `BBM`, etc.).
   - Effort input (numeric $> 0$) and Effort Units dropdown (`FHOURS`, `FDAYS`, `SETS`).
   - Month and Year pickers.
   - Interactive Leaflet / Mapbox map picker for Latitude & Longitude.
2. **Display Card**:
   - Primary metric: Predicted Catch in **Metric Tons (MT)**.
   - Confidence context / magnitude tier (e.g., Low, Medium, High).
   - Season tag automatically displayed (e.g., SW Monsoon).
   - Effort efficiency context (Estimated CPUE = Predicted Catch / Effort).

---

## 9. Model Limitations & Scientific Caveats

1. **Ocean Basin Domain**:
   - The model was trained on official IOTC surface fisheries catch and effort data covering the Indian Ocean and Arabian Sea (latitudes -44.5° to 29.5°, longitudes 20.5° to 149.5°). Extrapolation to the Atlantic or Pacific is unvalidated.
2. **Surface Gears**:
   - The dataset represents surface fishing fleets (Purse Seine, Baitboat, Ring Net). It does not represent deep longlines or deep demersal trawls.
3. **Observational Nature**:
   - Feature importances and regression weights represent empirical statistical correlations, not direct causal interventions. Catch depends on fish abundance, fleet dynamics, oceanographic currents, and SST anomalies.
4. **Extreme Events**:
   - Extremely high catches (>300 MT in a single stratum) exhibit higher absolute variance, though median absolute errors remain low (MedAE = 18.43 MT).
