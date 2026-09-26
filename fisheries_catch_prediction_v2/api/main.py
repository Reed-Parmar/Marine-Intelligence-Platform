"""
FastAPI service for Fisheries Catch Prediction V2.
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
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from fisheries_catch_prediction_v2.src.predict_v2 import FisheriesCatchPredictorV2


START_TIME = time.time()
PREDICTOR_V2: Optional[FisheriesCatchPredictorV2] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global PREDICTOR_V2
    try:
        model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "final_model"))
        PREDICTOR_V2 = FisheriesCatchPredictorV2(model_dir=model_dir)
        print("FisheriesCatchPredictorV2 successfully initialized.")
    except Exception as e:
        print(f"Warning: Failed to initialize FisheriesCatchPredictorV2 on startup: {e}")
    yield


app = FastAPI(
    title="Fisheries Catch Prediction API V2",
    description="V2 Machine Learning service for predicting continuous fisheries catch quantities (Metric Tons).",
    version="2.0.0",
    lifespan=lifespan
)


# Pydantic Schemas
class FisheriesCatchRequestV2(BaseModel):
    Fleet: str = Field(..., description="Fishing vessel flag state (e.g. EUESP, EUFRA, SYC, MDV, JPN)", json_schema_extra={"example": "EUESP"})
    Gear: str = Field(..., description="Fishing gear code (e.g. PS: Purse Seine, BB: Baitboat)", json_schema_extra={"example": "PS"})
    Effort: float = Field(..., ge=0.0, description="Fishing effort expended (must be non-negative)", json_schema_extra={"example": 45.0})
    EffortUnits: str = Field(..., description="Unit of effort (e.g. FHOURS, FDAYS, SETS, TRIPS)", json_schema_extra={"example": "FHOURS"})
    Month: int = Field(..., ge=1, le=12, description="Month of fishing operation (1-12)", json_schema_extra={"example": 8})
    Year: int = Field(..., ge=1970, le=2035, description="Year of fishing operation", json_schema_extra={"example": 2024})
    Latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)", json_schema_extra={"example": 12.5})
    Longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)", json_schema_extra={"example": 62.5})
    SpatialResolution: Optional[float] = Field(1.0, description="Spatial grid resolution in degrees (default 1.0)", json_schema_extra={"example": 1.0})


class CatchPredictionResponseV2(BaseModel):
    predicted_catch: float = Field(..., description="Predicted catch quantity in Metric Tons", json_schema_extra={"example": 365.81})
    unit: str = Field("Metric Tons (MT)", description="Measurement unit of catch")
    model: str = Field(..., description="Model architecture", json_schema_extra={"example": "XGBoost Regressor V2"})
    version: str = Field(..., description="Model version", json_schema_extra={"example": "2.0.0"})
    input_summary: dict


class BatchCatchRequestV2(BaseModel):
    items: List[FisheriesCatchRequestV2] = Field(..., description="List of fisheries catch prediction requests")


class BatchCatchResponseV2(BaseModel):
    total_records: int
    predictions: List[CatchPredictionResponseV2]


class HealthResponseV2(BaseModel):
    status: str
    uptime_seconds: float
    model_loaded: bool
    model_name: str
    version: str
    target_unit: str


@app.get("/health", response_model=HealthResponseV2, tags=["Monitoring"])
def health_check():
    """Health check endpoint confirming API status, model readiness, and uptime."""
    global PREDICTOR_V2
    loaded = PREDICTOR_V2 is not None and PREDICTOR_V2.model is not None
    return HealthResponseV2(
        status="healthy",
        uptime_seconds=round(time.time() - START_TIME, 2),
        model_loaded=loaded,
        model_name="IOTC Fisheries Catch Predictor V2",
        version="2.0.0",
        target_unit="Metric Tons (MT)"
    )


@app.get("/model-info", tags=["Metadata"])
def get_model_info():
    """Return V2 model metadata, validation and test metrics, and feature schema."""
    global PREDICTOR_V2
    if PREDICTOR_V2 is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not loaded.")
    return {
        "metadata": PREDICTOR_V2.metadata,
        "feature_schema": PREDICTOR_V2.schema
    }


@app.post("/predict", response_model=CatchPredictionResponseV2, tags=["Prediction"])
def predict_single(request: FisheriesCatchRequestV2):
    """Predict continuous catch quantity for a single fisheries operational event."""
    global PREDICTOR_V2
    if PREDICTOR_V2 is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not loaded.")
    try:
        req_dict = request.model_dump()
        res = PREDICTOR_V2.predict(req_dict)
        return CatchPredictionResponseV2(
            predicted_catch=res["predicted_catch_mt"],
            unit=res["unit"],
            model=res["model"],
            version=res["version"],
            input_summary=res["input_summary"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {e}")


@app.post("/predict/batch", response_model=BatchCatchResponseV2, tags=["Prediction"])
def predict_batch_endpoint(request: BatchCatchRequestV2):
    """Predict continuous catch quantities for a batch of fisheries operational events."""
    global PREDICTOR_V2
    if PREDICTOR_V2 is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not loaded.")
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch request cannot be empty.")
    try:
        items_dict = [item.model_dump() for item in request.items]
        preds = PREDICTOR_V2.predict_batch(items_dict)
        formatted = [
            CatchPredictionResponseV2(
                predicted_catch=p["predicted_catch_mt"],
                unit=p["unit"],
                model=p["model"],
                version=p["version"],
                input_summary=p["input_summary"]
            )
            for p in preds
        ]
        return BatchCatchResponseV2(total_records=len(formatted), predictions=formatted)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Batch inference error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fisheries_catch_prediction_v2.api.main:app", host="0.0.0.0", port=8002, reload=False)
