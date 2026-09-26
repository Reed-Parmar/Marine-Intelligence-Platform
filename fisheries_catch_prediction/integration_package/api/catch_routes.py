"""
FastAPI APIRouter for Fisheries Catch Prediction (Phase 14.3).
Designed for seamless, single-line plug-and-play mounting into the unified Marine Intelligence Platform:
    from integration_package.api.catch_routes import router as fisheries_router
    app.include_router(fisheries_router)
"""
import os
import sys
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Ensure inference module is accessible
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

from inference.predict import FisheriesCatchPredictor


router = APIRouter(prefix="/fisheries", tags=["Fisheries Catch Prediction"])

MODEL_DIR = os.path.join(pkg_root, "model")
PREDICTOR: Optional[FisheriesCatchPredictor] = None


def get_predictor() -> FisheriesCatchPredictor:
    """Lazy loader for predictor instance."""
    global PREDICTOR
    if PREDICTOR is None:
        PREDICTOR = FisheriesCatchPredictor(model_dir=MODEL_DIR)
    return PREDICTOR


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


@router.get("/health")
def fisheries_health():
    """Health status of the fisheries prediction component."""
    pred = get_predictor()
    return {
        "status": "healthy",
        "component": "Fisheries Catch Prediction (Phase 14.3)",
        "model_loaded": pred is not None and pred.model is not None,
        "target_unit": "Metric Tons (MT)"
    }


@router.get("/model-info")
def fisheries_model_info():
    """Detailed model metadata and input schema."""
    pred = get_predictor()
    return {
        "metadata": pred.metadata,
        "feature_schema": pred.schema
    }


@router.post("/predict", response_model=CatchPredictionResponse)
def predict_single_catch(request: FisheriesCatchRequest):
    """Predict expected catch in Metric Tons for a single operational stratum."""
    pred = get_predictor()
    try:
        res = pred.predict(request.model_dump())
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


@router.post("/predict/batch", response_model=BatchCatchResponse)
def predict_batch_catch(request: BatchCatchRequest):
    """Predict expected catches in Metric Tons for multiple operational strata."""
    pred = get_predictor()
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch items list cannot be empty.")
    try:
        items = [item.model_dump() for item in request.items]
        preds = pred.predict_batch(items)
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
