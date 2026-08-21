"""
Analysis Router: Scientific analysis jobs and cross-domain correlation hooks (Phase 6).
Queries real public.analysis_jobs and public.analysis_results tables via SQLAlchemy.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.db.database import execute_query, execute_single
from backend.app.schemas.analysis import (
    AnalysisJobResponse,
    CorrelationAnalysisRequest,
    CorrelationAnalysisResponse
)
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse

logger = logging.getLogger(__name__)
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


def _infer_domain(var_name: str, fallback_domain: Optional[str] = None) -> str:
    v = (var_name or "").lower()
    if any(k in v for k in ["temp", "salin", "oxygen", "ctd", "depth", "chlorophyll", "turbidity"]):
        return "oceanography"
    if any(k in v for k in ["catch", "cpue", "effort", "gear", "vessel", "landing"]):
        return "fisheries"
    if any(k in v for k in ["edna", "dna", "sequence"]):
        return "edna"
    if any(k in v for k in ["richness", "count", "shannon", "simpson", "species", "pielou"]):
        return "biodiversity"
    return fallback_domain or "oceanography"


@router.post("/correlation", response_model=ApiResponse[CorrelationAnalysisResponse])
async def run_correlation(req: CorrelationAnalysisRequest):
    """
    Cross-domain scientific correlation analysis hook (Phase 6).
    Invokes deterministic Phase 6 ScientificAnalysisService.
    """
    from data_pipeline.analysis.service import ScientificAnalysisService
    from data_pipeline.fusion.models import UnifiedQueryParams
    from data_pipeline.fusion.query_service import query_unified_observations

    var_x = req.variable_x or req.independentVariable
    var_y = req.variable_y or req.dependentVariable

    if not var_x or not var_y:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PARAMETERS", "message": "Both variable_x and variable_y must be provided."}
        )

    dom_x = req.domain_x or _infer_domain(var_x, "oceanography")
    dom_y = req.domain_y or _infer_domain(var_y, "fisheries")

    observations = None
    if req.date_from or req.date_to:
        params = UnifiedQueryParams(date_from=req.date_from, date_to=req.date_to)
        try:
            observations = query_unified_observations(params)
        except Exception as e:
            logger.warning(f"Failed to query date-filtered observations for correlation: {e}")
            observations = None

    try:
        res = ScientificAnalysisService.calculate_correlation(
            domain_x=dom_x,
            variable_x=var_x,
            domain_y=dom_y,
            variable_y=var_y,
            observations=observations,
            method=req.method or "pearson",
            spatial_radius_km=req.spatial_radius_km,
            temporal_window_hours=req.temporal_window_hours,
            depth_tolerance_m=req.depth_tolerance_m
        )
    except Exception as e:
        logger.error(f"Scientific correlation computation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ANALYSIS_FAILED", "message": "Scientific correlation computation failed."}
        )

    # Format scatter points and regression line for frontend visualization
    scatter_points = []
    x_vals = []
    for p in res.paired_data:
        x_val = p.get("x")
        y_val = p.get("y")
        if x_val is not None and y_val is not None:
            scatter_points.append({
                "x": float(x_val),
                "y": float(y_val),
                "stationId": p.get("station_id"),
                "depth": p.get("depth"),
                "latitude": p.get("latitude"),
                "longitude": p.get("longitude")
            })
            x_vals.append(float(x_val))

    x_min = min(x_vals) if x_vals else 0.0
    x_max = max(x_vals) if x_vals else 10.0
    res_dict = res.to_dict()
    slope = float(res_dict.get("slope") or 0.0)
    intercept = float(res_dict.get("intercept") or 0.0)
    r_sq = float(res_dict.get("r_squared") or (res.correlation_coefficient ** 2 if res.correlation_coefficient is not None else 0.0))
    p_val = res.p_value  # Preserve None if unavailable

    statistics = {
        "sampleSize": res.sample_size,
        "pearsonR": res.correlation_coefficient if res.correlation_coefficient is not None else 0.0,
        "rSquared": r_sq,
        "pValue": p_val,
        "standardError": float(res_dict.get("std_err") or 0.0),
        "fStatistic": 0.0,
        "slope": slope,
        "intercept": intercept
    }

    regression_line = {
        "xMin": x_min,
        "xMax": x_max,
        "yAtMin": round(slope * x_min + intercept, 4),
        "yAtMax": round(slope * x_max + intercept, 4)
    }

    response_data = CorrelationAnalysisResponse(
        id=f"analysis-{var_x}-{var_y}",
        title=f"{var_x.replace('_', ' ').title()} vs {var_y.replace('_', ' ').title()} Correlation",
        variable_x=var_x,
        variable_y=var_y,
        domain_x=dom_x,
        domain_y=dom_y,
        method=res.method,
        correlation_coefficient=res.correlation_coefficient,
        sample_size=res.sample_size,
        p_value=res.p_value,
        interpretation=res.interpretation,
        is_statistically_significant=res.is_statistically_significant,
        disclaimer=res.disclaimer,
        data_points=res.paired_data,
        scatterPoints=scatter_points,
        statistics=statistics,
        regressionLine=regression_line,
        ecologicalInterpretation=f"{res.interpretation}. {res.disclaimer}",
        provenance={
            "algorithmName": f"Phase 6 {res.method.title()} Cross-Domain Correlation",
            "recordsUsedCount": res.sample_size,
            "domainX": dom_x,
            "domainY": dom_y
        },
        warnings=res.warnings
    )

    return ApiResponse(data=response_data)


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
