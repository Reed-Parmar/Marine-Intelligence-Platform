"""
Standalone FastAPI service for Fisheries Catch Prediction (Phase 14.3).
Provides endpoints:
- GET /health
- GET /model-info
- POST /predict
- POST /predict/batch
"""
import os
import sys
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from fisheries_catch_prediction.src.predict import FisheriesCatchPredictor


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    global PREDICTOR
    try:
        model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "final_model"))
        PREDICTOR = FisheriesCatchPredictor(model_dir=model_dir)
        print("FisheriesCatchPredictor successfully initialized.")
    except Exception as e:
        print(f"Warning: Failed to initialize FisheriesCatchPredictor on startup: {e}")
    yield


# Initialize FastAPI app
app = FastAPI(
    title="Fisheries Catch Prediction API",
    description="Standalone ML service for predicting fisheries catch quantities (Metric Tons) from operational parameters.",
    version="1.0.0",
    lifespan=lifespan
)

START_TIME = time.time()
PREDICTOR: Optional[FisheriesCatchPredictor] = None


# Pydantic Schemas
class FisheriesCatchRequest(BaseModel):
    Fleet: str = Field(..., description="Fishing vessel flag state (e.g. EUESP, EUFRA, SYC, MDV, JPN)", json_schema_extra={"example": "EUESP"})
    Gear: str = Field(..., description="Fishing gear code (e.g. PS: Purse Seine, BB: Baitboat)", json_schema_extra={"example": "PS"})
    Effort: float = Field(..., ge=0.0, description="Fishing effort expended (must be non-negative)", json_schema_extra={"example": 45.0})
    EffortUnits: str = Field(..., description="Unit of effort (e.g. FHOURS, FDAYS, SETS, TRIPS)", json_schema_extra={"example": "FHOURS"})
    Month: int = Field(..., ge=1, le=12, description="Month of fishing operation (1-12)", json_schema_extra={"example": 8})
    Year: int = Field(..., ge=1970, le=2035, description="Year of fishing operation", json_schema_extra={"example": 2024})
    Latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)", json_schema_extra={"example": 2.5})
    Longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)", json_schema_extra={"example": 55.5})
    SpatialResolution: Optional[float] = Field(1.0, description="Spatial grid resolution in degrees (default 1.0)", json_schema_extra={"example": 1.0})


class CatchPredictionResponse(BaseModel):
    predicted_catch: float = Field(..., description="Predicted catch quantity in Metric Tons", json_schema_extra={"example": 108.83})
    unit: str = Field("Metric Tons (MT)", description="Measurement unit of catch")
    model: str = Field(..., description="Model architecture", json_schema_extra={"example": "XGBoost Regressor (Tuned)"})
    model_version: str = Field(..., description="Model version", json_schema_extra={"example": "1.0.0"})
    input_summary: dict


class BatchCatchRequest(BaseModel):
    items: List[FisheriesCatchRequest] = Field(..., description="List of fisheries catch prediction requests")


class BatchCatchResponse(BaseModel):
    total_records: int
    predictions: List[CatchPredictionResponse]


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    model_loaded: bool
    model_name: str
    target_unit: str


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check():
    """Health check endpoint confirming API status, model readiness, and uptime."""
    global PREDICTOR
    loaded = PREDICTOR is not None and PREDICTOR.model is not None
    return HealthResponse(
        status="healthy",
        uptime_seconds=round(time.time() - START_TIME, 2),
        model_loaded=loaded,
        model_name="XGBoost Regressor (Tuned)",
        target_unit="Metric Tons (MT)"
    )


@app.get("/model-info", tags=["Metadata"])
def get_model_info():
    """Return model metadata, training periods, validation & test metrics, and feature schema."""
    global PREDICTOR
    if PREDICTOR is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not loaded.")
    return {
        "metadata": PREDICTOR.metadata,
        "feature_schema": PREDICTOR.schema
    }


@app.post("/predict", response_model=CatchPredictionResponse, tags=["Prediction"])
def predict_single(request: FisheriesCatchRequest):
    """Predict continuous catch quantity for a single fisheries operational event."""
    global PREDICTOR
    if PREDICTOR is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not loaded.")
    try:
        req_dict = request.model_dump()
        res = PREDICTOR.predict(req_dict)
        return CatchPredictionResponse(
            predicted_catch=res["predicted_catch_mt"],
            unit=res["unit"],
            model=res["model"],
            model_version=res["model_version"],
            input_summary=res["input_summary"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {e}")


@app.post("/predict/batch", response_model=BatchCatchResponse, tags=["Prediction"])
def predict_batch_endpoint(request: BatchCatchRequest):
    """Predict continuous catch quantities for a batch of fisheries operational events."""
    global PREDICTOR
    if PREDICTOR is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not loaded.")
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch request cannot be empty.")
    try:
        items_dict = [item.model_dump() for item in request.items]
        preds = PREDICTOR.predict_batch(items_dict)
        formatted = [
            CatchPredictionResponse(
                predicted_catch=p["predicted_catch_mt"],
                unit=p["unit"],
                model=p["model"],
                model_version=p["model_version"],
                input_summary=p["input_summary"]
            )
            for p in preds
        ]
        return BatchCatchResponse(total_records=len(formatted), predictions=formatted)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Batch inference error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fisheries_catch_prediction.api.main:app", host="0.0.0.0", port=8001, reload=False)
