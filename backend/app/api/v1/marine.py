"""
Unified Marine Router: Cross-domain queries and aggregated summaries.
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.marine import (
    CrossDomainLocationDetailResponse,
    MarineObservationItem,
    MarineQueryRequest,
    MarineSummaryResponse
)
from backend.app.services.marine_service import MarineService

router = APIRouter()


@router.get("/observations", response_model=ApiListResponse[MarineObservationItem])
def get_marine_observations(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    dataset_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Returns unified observations across oceanography, fisheries, and biodiversity.
    """
    items, total = MarineService.get_unified_observations(
        date_from=date_from,
        date_to=date_to,
        dataset_id=dataset_id,
        page=page,
        page_size=page_size
    )
    return ApiListResponse(
        data=items,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/summary", response_model=ApiResponse[MarineSummaryResponse])
def get_marine_summary():
    """
    Returns unified summary counts across all marine datasets and domains.
    """
    res = MarineService.get_marine_summary()
    return ApiResponse(data=res)


@router.post("/query", response_model=ApiListResponse[MarineObservationItem])
def query_marine(req: MarineQueryRequest):
    """
    Executes a structured spatial/temporal cross-domain marine query.
    """
    items, total = MarineService.query_marine(req)
    return ApiListResponse(
        data=items,
        meta=ApiMeta(page=req.page, page_size=req.page_size, total=total)
    )


@router.get("/location-detail", response_model=ApiResponse[CrossDomainLocationDetailResponse])
def get_location_detail(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    radius_km: float = Query(50.0, ge=1.0, le=500.0),
    temporal_window_hours: float = Query(72.0, ge=1.0),
    depth_tolerance_m: float = Query(50.0, ge=1.0)
):
    """
    Discovers associated observations across all domains near a geographic point using Phase 5 Fusion engine.
    """
    res = MarineService.get_location_detail(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        temporal_window_hours=temporal_window_hours,
        depth_tolerance_m=depth_tolerance_m
    )
    return ApiResponse(data=res)
