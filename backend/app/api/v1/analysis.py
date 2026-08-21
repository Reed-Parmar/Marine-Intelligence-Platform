"""
Analysis Router: Scientific analysis jobs and cross-domain correlation hooks (Phase 6).
Queries real public.analysis_jobs and public.analysis_results tables via SQLAlchemy.
"""

import json
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.db.database import execute_query, execute_single, execute_write
from backend.app.schemas.analysis import (
    AnalysisJobResponse,
    CorrelationAnalysisRequest,
    CorrelationAnalysisResponse
)
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ApiListResponse[AnalysisJobResponse])
def list_analyses(
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
            job_type=str(r.get("analysis_type") or r.get("job_type", "correlation")),
            status=str(r.get("status", "completed")),
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
def run_correlation(req: CorrelationAnalysisRequest):
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
        logger.exception("Correlation computation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ANALYSIS_ERROR", "message": f"Scientific correlation computation failed: {str(e)}"}
        )

    # Compute regression line coordinates
    scatter_points = []
    x_vals = []
    y_vals = []
    for item in res.paired_data:
        x_val = item.get("x") or item.get("variable_x") or item.get(var_x)
        y_val = item.get("y") or item.get("variable_y") or item.get(var_y)
        if x_val is not None and y_val is not None:
            try:
                xf = float(x_val)
                yf = float(y_val)
                scatter_points.append({"x": xf, "y": yf})
                x_vals.append(xf)
                y_vals.append(yf)
            except (ValueError, TypeError):
                continue

    slope = 0.0
    intercept = 0.0
    if len(x_vals) >= 2:
        mean_x = sum(x_vals) / len(x_vals)
        mean_y = sum(y_vals) / len(y_vals)
        denom = sum((x - mean_x) ** 2 for x in x_vals)
        if denom > 1e-9:
            slope = round(sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals)) / denom, 4)
            intercept = round(mean_y - slope * mean_x, 4)

    x_min = min(x_vals) if x_vals else 0.0
    x_max = max(x_vals) if x_vals else 1.0

    coeff = res.correlation_coefficient if res.correlation_coefficient is not None else 0.0
    r_sq = round(coeff ** 2, 4)

    statistics = {
        "pearsonR": coeff,
        "r2": r_sq,
        "pValue": res.p_value,
        "sampleSize": res.sample_size,
        "slope": slope,
        "intercept": intercept
    }

    regression_line = {
        "xMin": x_min,
        "xMax": x_max,
        "yAtMin": round(slope * x_min + intercept, 4),
        "yAtMax": round(slope * x_max + intercept, 4)
    }

    job_id = str(uuid.uuid4())
    try:
        execute_write(
            """
            INSERT INTO public.analysis_jobs (
                id, analysis_type, name, description, status, parameters, created_at, completed_at
            ) VALUES (
                CAST(:id AS uuid), :type, :name, :description, 'completed'::analysis_status, CAST(:params AS jsonb), NOW(), NOW()
            );
            """,
            {
                "id": job_id,
                "type": "cross_domain_correlation",
                "name": f"{var_x.replace('_', ' ').title()} vs {var_y.replace('_', ' ').title()} Correlation",
                "description": f"Cross-domain correlation analysis between {var_x} and {var_y}.",
                "params": json.dumps({
                    "variable_x": var_x,
                    "variable_y": var_y,
                    "domain_x": dom_x,
                    "domain_y": dom_y,
                    "method": req.method or "pearson",
                    "pearson_r": coeff,
                    "r_squared": r_sq,
                    "sample_size": res.sample_size
                })
            }
        )
    except Exception as db_err:
        logger.warning("Could not persist analysis_jobs audit record: %s", db_err)

    response_data = CorrelationAnalysisResponse(
        id=f"analysis-{var_x.replace('_', '-')}-{var_y.replace('_', '-')}",
        title=f"{var_x.replace('_', ' ').title()} vs {var_y.replace('_', ' ').title()} Correlation",
        variable_x=var_x,
        variable_y=var_y,
        domain_x=dom_x,
        domain_y=dom_y,
        method=res.method,
        correlation_coefficient=coeff,
        pearson_r=coeff,
        r_squared=r_sq,
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
            "jobId": job_id,
            "algorithmName": f"Phase 6 {res.method.title()} Cross-Domain Correlation",
            "recordsUsedCount": res.sample_size,
            "domainX": dom_x,
            "domainY": dom_y
        },
        warnings=res.warnings
    )

    return ApiResponse(data=response_data)


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str):
    """
    Retrieves scientific analysis data or job status.
    Seamlessly handles canonical slugs (e.g. analysis-sst-richness) and database job UUIDs.
    """
    # 1. Handle canonical scientific analysis slugs
    slug_mappings = {
        "analysis-sst-richness": ("sea_surface_temperature", "species_richness"),
        "sst-richness": ("sea_surface_temperature", "species_richness"),
        "analysis-oxygen-cpue": ("dissolved_oxygen", "cpue"),
        "oxygen-cpue": ("dissolved_oxygen", "cpue"),
        "analysis-salinity-biodiversity": ("salinity", "species_richness"),
        "salinity-biodiversity": ("salinity", "species_richness"),
    }
    if analysis_id in slug_mappings:
        var_x, var_y = slug_mappings[analysis_id]
        return run_correlation(CorrelationAnalysisRequest(
            variable_x=var_x,
            variable_y=var_y
        ))

    # 2. Check if valid UUID for database lookup
    is_valid_uuid = False
    clean_uuid = None
    try:
        clean_uuid = str(uuid.UUID(str(analysis_id).strip()))
        is_valid_uuid = True
    except (ValueError, TypeError, AttributeError):
        is_valid_uuid = False

    if is_valid_uuid and clean_uuid:
        r = execute_single(
            "SELECT * FROM public.analysis_jobs WHERE id = CAST(:analysis_id AS uuid);",
            {"analysis_id": clean_uuid}
        )
        if r:
            return ApiResponse(
                data=AnalysisJobResponse(
                    id=str(r["id"]),
                    job_type=r.get("analysis_type") or r.get("job_type", "correlation"),
                    status=str(r.get("status", "completed")),
                    parameters=r.get("parameters"),
                    created_at=str(r["created_at"]) if r.get("created_at") else None,
                    completed_at=str(r["completed_at"]) if r.get("completed_at") else None
                )
            )

    # 3. Dynamic slug fallback (e.g. analysis-temperature-catch)
    if analysis_id.startswith("analysis-"):
        parts = analysis_id.replace("analysis-", "").split("-")
        if len(parts) >= 2:
            return run_correlation(CorrelationAnalysisRequest(
                variable_x=parts[0],
                variable_y=parts[1]
            ))

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "JOB_NOT_FOUND", "message": f"Analysis job or template '{analysis_id}' not found."}
    )

