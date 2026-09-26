"""
Fisheries Router: Catch logs, effort statistics, gear summaries, and catch trends.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.fisheries import (
    BatchCatchRequest,
    BatchCatchResponse,
    CatchPredictionResponse,
    FisheriesCatchRequest,
    FisheriesModelInfoResponse,
    FisheriesObservationResponse,
    FisheriesSummaryResponse,
    FisheriesTrendResponse,
)
from backend.app.services.fisheries_service import FisheriesService
from ml.fisheries_catch import (
    FisheriesCatchPredictor,
    get_fisheries_predictor,
    predict_catch,
)

router = APIRouter()


@router.get("/observations", response_model=ApiListResponse[FisheriesObservationResponse])
async def list_fisheries_observations(
    dataset_id: Optional[str] = Query(None),
    species_id: Optional[str] = Query(None),
    fishing_zone: Optional[str] = Query(None),
    gear_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Returns fisheries catch records with species, zone, and gear filters.
    """
    observations, total = FisheriesService.list_observations(
        dataset_id=dataset_id,
        species_id=species_id,
        fishing_zone=fishing_zone,
        gear_type=gear_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    return ApiListResponse(
        data=observations,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/observations/{observation_id}", response_model=ApiResponse[FisheriesObservationResponse])
async def get_fisheries_observation(observation_id: str):
    """
    Retrieves a single fisheries catch record by ID.
    """
    obs = FisheriesService.get_observation_by_id(observation_id)
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OBSERVATION_NOT_FOUND", "message": f"Fisheries observation '{observation_id}' not found."}
        )
    return ApiResponse(data=obs)


@router.get("/summary", response_model=ApiResponse[FisheriesSummaryResponse])
async def get_fisheries_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """
    Returns aggregate fisheries statistics (total catch, average catch, total effort hours, distinct species).
    """
    summary = FisheriesService.get_fisheries_summary(date_from=date_from, date_to=date_to)
    return ApiResponse(data=summary)


@router.get("/trends", response_model=ApiResponse[FisheriesTrendResponse])
async def get_fisheries_trends(
    interval: str = Query("month"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """
    Returns time-series catch weight and effort trends.
    """
    trends = FisheriesService.get_fisheries_trends(
        interval=interval,
        date_from=date_from,
        date_to=date_to
    )
    return ApiResponse(data=trends)


# ==============================================================================
# PHASE 14.3: FISHERIES CATCH PREDICTION V1 ENDPOINTS (XGBoost TotalCatchMT)
# ==============================================================================

@router.post("/predict", response_model=ApiResponse[CatchPredictionResponse])
async def predict_fisheries_catch(request: FisheriesCatchRequest):
    """
    Predicts commercial marine fisheries catch in Metric Tons (MT) for a given operational stratum (Phase 14.3 V1).
    Uses tuned XGBoost regressor targeting TotalCatchMT with IOTC surface fisheries feature engineering.
    """
    try:
        predictor = get_fisheries_predictor()
        res = predictor.predict(request.model_dump())
        return ApiResponse(
            data=CatchPredictionResponse(
                predicted_catch=res["predicted_catch_mt"],
                predicted_catch_mt=res["predicted_catch_mt"],
                unit=res["unit"],
                target_variable=res.get("target_variable", "TotalCatchMT"),
                model=res["model"],
                model_version=res["model_version"],
                disclaimer=res.get(
                    "disclaimer",
                    "Predicted catch is an estimated expectation based on historical IOTC surface fisheries operational strata and not a guaranteed actual harvest."
                ),
                input_summary=res["input_summary"]
            )
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(ve)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INFERENCE_ERROR", "message": f"Fisheries catch prediction error: {str(e)}"}
        )


@router.post("/predict/batch", response_model=ApiResponse[BatchCatchResponse])
async def predict_fisheries_catch_batch(request: BatchCatchRequest):
    """
    Predicts commercial marine fisheries catch in Metric Tons for multiple operational strata (Phase 14.3 V1).
    """
    if not request.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_BATCH", "message": "Batch items list cannot be empty."}
        )
    try:
        predictor = get_fisheries_predictor()
        items = [item.model_dump() for item in request.items]
        preds = predictor.predict_batch(items)
        formatted = [
            CatchPredictionResponse(
                predicted_catch=p["predicted_catch_mt"],
                predicted_catch_mt=p["predicted_catch_mt"],
                unit=p["unit"],
                target_variable=p.get("target_variable", "TotalCatchMT"),
                model=p["model"],
                model_version=p["model_version"],
                disclaimer=p.get(
                    "disclaimer",
                    "Predicted catch is an estimated expectation based on historical IOTC surface fisheries operational strata and not a guaranteed actual harvest."
                ),
                input_summary=p["input_summary"]
            )
            for p in preds
        ]
        return ApiResponse(data=BatchCatchResponse(total_records=len(formatted), predictions=formatted))
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(ve)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "BATCH_INFERENCE_ERROR", "message": f"Batch prediction error: {str(e)}"}
        )


@router.get("/predict/model-info", response_model=ApiResponse[FisheriesModelInfoResponse])
@router.get("/model-info", response_model=ApiResponse[FisheriesModelInfoResponse])
async def get_fisheries_model_info():
    """
    Returns production V1 model metadata and feature schema (Phase 14.3 V1).
    """
    predictor = get_fisheries_predictor()
    return ApiResponse(
        data=FisheriesModelInfoResponse(
            metadata=predictor.metadata,
            feature_schema=predictor.schema
        )
    )


@router.get("/predict/health")
@router.get("/health")
async def fisheries_prediction_health():
    """
    Health check endpoint for Fisheries Catch Prediction V1 component.
    """
    predictor = get_fisheries_predictor()
    return {
        "status": "ready",
        "component": "Fisheries Catch Prediction V1 (Phase 14.3)",
        "model_version": predictor.metadata.get("model_version", "1.0.0"),
        "target_variable": "TotalCatchMT",
        "target_units": "Metric Tons (MT)",
        "model_loaded": predictor.is_loaded
    }

