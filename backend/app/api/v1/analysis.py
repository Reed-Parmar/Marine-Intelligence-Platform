"""
Analysis Router: Scientific analysis jobs and cross-domain correlation hooks (Phase 6).
Queries real public.analysis_jobs and public.analysis_results tables via SQLAlchemy.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.db.database import execute_query, execute_single
from backend.app.schemas.analysis import (
    AnalysisJobResponse,
    CorrelationAnalysisRequest,
    CorrelationAnalysisResponse
)
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse

router = APIRouter()


@router.get("", response_model=ApiListResponse[AnalysisJobResponse])
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lists executed scientific analysis tasks from public.analysis_jobs.
    """
    count_res = execute_single("SELECT COUNT(*) as total FROM public.analysis_jobs;")
    total = count_res["total"] if count_res else 0

    offset = (page - 1) * page_size
    rows = execute_query(
        "SELECT * FROM public.analysis_jobs ORDER BY created_at DESC LIMIT :limit OFFSET :offset;",
        {"limit": page_size, "offset": offset}
    )
    jobs = [
        AnalysisJobResponse(
            id=str(r["id"]),
            job_type=r["job_type"],
            status=r["status"],
            parameters=r.get("parameters"),
            created_at=str(r["created_at"]) if r.get("created_at") else None,
            completed_at=str(r["completed_at"]) if r.get("completed_at") else None
        )
        for r in rows
    ]
    return ApiListResponse(
        data=jobs,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.post("/correlation", response_model=ApiResponse[CorrelationAnalysisResponse])
async def run_correlation(req: CorrelationAnalysisRequest):
    """
    Cross-domain scientific correlation analysis hook (Phase 6).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "ANALYSIS_MODULE_PENDING",
            "message": "Cross-domain scientific correlation analysis (Phase 6) is pending integration of the statistical compute module."
        }
    )


@router.get("/{analysis_id}", response_model=ApiResponse[AnalysisJobResponse])
async def get_analysis_job(analysis_id: str):
    """
    Retrieves status and metadata for an analysis job from database.
    """
    r = execute_single(
        "SELECT * FROM public.analysis_jobs WHERE id = :analysis_id;",
        {"analysis_id": analysis_id}
    )
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Analysis job '{analysis_id}' not found."}
        )
    return ApiResponse(
        data=AnalysisJobResponse(
            id=str(r["id"]),
            job_type=r["job_type"],
            status=r["status"],
            parameters=r.get("parameters"),
            created_at=str(r["created_at"]) if r.get("created_at") else None,
            completed_at=str(r["completed_at"]) if r.get("completed_at") else None
        )
    )
