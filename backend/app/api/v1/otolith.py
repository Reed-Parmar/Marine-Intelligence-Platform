"""
Otolith Router: Fish specimen imagery and morphology analysis hooks.
Queries real public.otolith_samples and public.otolith_results via SQLAlchemy.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.db.database import execute_query, execute_single
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.otolith import OtolithAnalysisResponse, OtolithSampleResponse

router = APIRouter()


@router.get("/samples", response_model=ApiListResponse[OtolithSampleResponse])
async def list_otolith_samples(
    dataset_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lists otolith fish specimens and associated microscope imagery from database.
    """
    conditions = []
    params: Dict[str, Any] = {}
    if dataset_id:
        conditions.append("dataset_id = :dataset_id")
        params["dataset_id"] = dataset_id
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    count_res = execute_single(f"SELECT COUNT(*) as total FROM public.otolith_samples {where_clause};", params)
    total = count_res["total"] if count_res else 0

    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset
    rows = execute_query(
        f"SELECT * FROM public.otolith_samples {where_clause} ORDER BY created_at DESC LIMIT :limit OFFSET :offset;",
        params
    )
    samples = [
        OtolithSampleResponse(
            id=str(r["id"]),
            dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
            fish_specimen_id=r.get("fish_specimen_id"),
            image_storage_path=r.get("image_storage_path"),
            fish_length_cm=float(r["fish_length_cm"]) if r.get("fish_length_cm") is not None else None,
            fish_weight_g=float(r["fish_weight_g"]) if r.get("fish_weight_g") is not None else None,
            estimated_age_years=float(r["estimated_age_years"]) if r.get("estimated_age_years") is not None else None,
            metadata=r.get("metadata")
        )
        for r in rows
    ]
    return ApiListResponse(
        data=samples,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.post("/analyse", response_model=ApiResponse[OtolithAnalysisResponse])
async def analyze_otolith(sample_id: str):
    """
    Otolith ring/annuli computer vision analysis hook (Phase 7).
    """
    # Check if sample exists in DB
    sample = execute_single("SELECT id FROM public.otolith_samples WHERE id = :sample_id;", {"sample_id": sample_id})
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SAMPLE_NOT_FOUND", "message": f"Otolith sample '{sample_id}' not found."}
        )

    # Automated ring detection is part of Phase 7 (Otolith Computer Vision pipeline)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "OTOLITH_MODULE_PENDING",
            "message": "Otolith automated annuli/age estimation (Phase 7) is pending integration of the CV model."
        }
    )


@router.get("/analyses/{analysis_id}", response_model=ApiResponse[OtolithAnalysisResponse])
async def get_otolith_analysis(analysis_id: str):
    """
    Retrieves an otolith analysis result from public.otolith_results.
    """
    r = execute_single(
        "SELECT * FROM public.otolith_results WHERE id = :analysis_id;",
        {"analysis_id": analysis_id}
    )
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Otolith analysis '{analysis_id}' not found."}
        )
    return ApiResponse(
        data=OtolithAnalysisResponse(
            analysis_id=str(r["id"]),
            sample_id=str(r["sample_id"]),
            status="completed",
            estimated_age_years=float(r["estimated_age_years"]) if r.get("estimated_age_years") is not None else None,
            confidence_score=float(r["confidence_score"]) if r.get("confidence_score") is not None else None,
            annuli_count=r.get("annuli_count"),
            created_at=str(r["created_at"]) if r.get("created_at") else None
        )
    )
