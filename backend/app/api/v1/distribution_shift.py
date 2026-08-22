"""
FastAPI Router for Seasonal Species Distribution Shift & Movement Propensity Prediction.

Scientific Scope:
- Eulerian population-level seasonal distribution shift prediction across 7 canonical Arabian Sea sectors.
- Strictly provides spatial decision support; does not model individual fish trajectories or telemetry.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.distribution_shift import (
    DistributionShiftPredictionRequest,
    DistributionShiftPredictionResponse,
)
from ml.distribution_shift.inference import predict_distribution_shift

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/predict",
    response_model=DistributionShiftPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Seasonal Species Distribution Shift",
    description="""
Forecasts population-level seasonal species distribution shifts and movement propensity across the 7 canonical Arabian Sea ecological sectors.

### Methodology & Model:
- **Architecture**: Full XGBoost multi-class classifier conditioned on spatial coordinates, bathymetric depth, cyclical monsoon month phase, available physicochemical CTD sensor profiles, and leak-free empirical Markov priors.
- **Target Space**: 7 Canonical Ecological Sectors (Malabar Shelf, Lakshadweep, Gujarat Shelf, Konkan Coast, Wadge Bank, Central Basin, SE EEZ).
- **Missing Sensor Handling**: Missing CTD parameters (`sst`, `salinity`, `do`, `chlorophyll`) are preserved natively as NaN and routed through decision trees without artificial zero-imputation.

### Empirically Calibrated Confidence Tiers:
- **HIGH** ($P \ge 0.70$): Strong historical and environmental agreement (empirical accuracy ~65–75%).
- **MODERATE** ($0.40 \le P < 0.70$): Clear seasonal dispersal signal with moderate uncertainty.
- **LOW** ($P < 0.40$): High uncertainty with broad probabilistic spread across sectors.

### Scientific Limitation:
*Population-level distribution prediction for spatial fisheries planning; not individual fish telemetry tracking.*
    """,
    responses={
        200: {
            "description": "Successful probabilistic distribution shift forecast.",
            "content": {
                "application/json": {
                    "example": {
                        "species": "Sardinella longiceps",
                        "prediction_type": "seasonal_distribution_shift",
                        "source_sector": "Malabar Upwelling Shelf",
                        "source_coordinates": {"latitude": 10.5, "longitude": 75.5},
                        "forecast_horizon_months": 2,
                        "forecast": {
                            "source_month": 4,
                            "target_month": 6,
                            "source_season": {"season_code": 1, "season_name": "Pre-Monsoon (Feb-May)"},
                            "target_season": {"season_code": 2, "season_name": "SW Monsoon (Jun-Sep)"}
                        },
                        "top_prediction": {"sector": "Malabar Upwelling Shelf", "probability": 0.5765, "centroid": [10.5, 75.5]},
                        "top_3_predictions": [
                            {"sector": "Malabar Upwelling Shelf", "probability": 0.5765, "centroid": [10.5, 75.5]},
                            {"sector": "Konkan Coast / Central West Coast", "probability": 0.2340, "centroid": [16.5, 73.0]},
                            {"sector": "Lakshadweep Sea & Ridge", "probability": 0.1297, "centroid": [10.5, 72.5]}
                        ],
                        "probability_distribution": {
                            "Malabar Upwelling Shelf": 0.5765,
                            "Central Arabian Sea Offshore Basin": 0.0089,
                            "North Arabian Sea / Gujarat Shelf": 0.0049,
                            "Lakshadweep Sea & Ridge": 0.1297,
                            "Wadge Bank / Comorin Sector": 0.0435,
                            "Konkan Coast / Central West Coast": 0.2340,
                            "South-Eastern Arabian Sea EEZ": 0.0025
                        },
                        "confidence_level": "MODERATE",
                        "confidence_tier": "Moderate confidence (Seasonal dispersal signal present)",
                        "environmental_context_available": True,
                        "environmental_inputs": {
                            "sst_celsius": 29.5,
                            "salinity_psu": 35.2,
                            "dissolved_oxygen_mgl": 4.8,
                            "chlorophyll_mg_m3": 1.5,
                            "mean_depth_meters": 35.0
                        },
                        "markov_baseline_comparison": {
                            "top_markov_sector": "Malabar Upwelling Shelf",
                            "markov_probability": 0.5429,
                            "fallback_level": 1,
                            "fallback_description": "Level 1: Exact Species + Sector + Season + Delta_T"
                        },
                        "model_metadata": {
                            "model_version": "3.0.0-full-xgboost-oof",
                            "training_period": "Historical surveys through 2023-12-31 (N=2,577 transitions)"
                        },
                        "limitations": [
                            "Population-level distribution prediction; not individual fish tracking."
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid input parameter or out-of-bounds coordinates."},
        404: {"description": "Requested species not found in trained taxonomic vocabulary."},
        422: {"description": "Request validation failure (e.g. malformed data types)."},
        500: {"description": "Internal model execution or inference error."},
    }
)
async def predict_species_distribution_shift(
    request: DistributionShiftPredictionRequest,
) -> DistributionShiftPredictionResponse:
    """
    Executes seasonal distribution shift prediction for a given species and spatial-temporal state.
    """
    try:
        # Convert Pydantic request to dictionary for inference engine
        payload = request.model_dump()

        # Delegate purely to inference engine without duplicating ML logic in the API layer
        prediction_result = predict_distribution_shift(payload)

        return DistributionShiftPredictionResponse(**prediction_result)

    except ValueError as val_err:
        err_msg = str(val_err)
        logger.warning(f"Validation error in distribution shift prediction: {err_msg}")
        if "not in the trained species vocabulary" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )

    except Exception as exc:
        logger.error(f"Unexpected error executing distribution shift prediction: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while executing the distribution shift prediction model.",
        )
