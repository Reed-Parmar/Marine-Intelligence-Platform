"""
ML Router: Machine learning model metadata and inference hooks (Phase 8).
Queries real public.ml_models and public.predictions tables via SQLAlchemy.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.db.database import execute_query, execute_single
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.ml import MLModelResponse, MLPredictRequest, MLPredictResponse

router = APIRouter()


@router.get("/models", response_model=ApiListResponse[MLModelResponse])
async def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lists deployed machine learning models registered in public.ml_models.
    """
    count_res = execute_single("SELECT COUNT(*) as total FROM public.ml_models;")
    total = count_res["total"] if count_res else 0

    offset = (page - 1) * page_size
    rows = execute_query(
        "SELECT * FROM public.ml_models WHERE is_active = TRUE ORDER BY created_at DESC LIMIT :limit OFFSET :offset;",
        {"limit": page_size, "offset": offset}
    )
    models = [
        MLModelResponse(
            model_id=str(r["id"]),
            name=r["name"],
            version=r["version"],
            task_type=r["model_type"],
            target_variable=r.get("target_variable"),
            input_features=r.get("metadata", {}).get("features", []) if isinstance(r.get("metadata"), dict) else [],
            status="active" if r.get("is_active") else "inactive",
            metrics=r.get("metadata", {}).get("metrics") if isinstance(r.get("metadata"), dict) else None
        )
        for r in rows
    ]
    return ApiListResponse(
        data=models,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/models/{model_id}", response_model=ApiResponse[MLModelResponse])
async def get_model(model_id: str):
    """
    Retrieves metadata for a specific model from public.ml_models.
    """
    r = execute_single("SELECT * FROM public.ml_models WHERE id = :model_id;", {"model_id": model_id})
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MODEL_NOT_FOUND", "message": f"ML model '{model_id}' not found."}
        )
    return ApiResponse(
        data=MLModelResponse(
            model_id=str(r["id"]),
            name=r["name"],
            version=r["version"],
            task_type=r["model_type"],
            target_variable=r.get("target_variable"),
            input_features=r.get("metadata", {}).get("features", []) if isinstance(r.get("metadata"), dict) else [],
            status="active" if r.get("is_active") else "inactive",
            metrics=r.get("metadata", {}).get("metrics") if isinstance(r.get("metadata"), dict) else None
        )
    )


@router.post("/predict", response_model=ApiResponse[MLPredictResponse])
async def predict(req: MLPredictRequest):
    """
    Machine learning model inference hook (Phase 8).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "ML_MODULE_PENDING",
            "message": f"Inference for model '{req.model_id}' (Phase 8) is pending model training and deployment."
        }
    )
