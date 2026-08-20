"""
Oceanography Router: CTD observations, physical parameter trends, and summary statistics.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.ocean import (
    OceanObservationResponse,
    OceanSummaryResponse,
    OceanTrendResponse
)
from backend.app.services.ocean_service import OceanService

router = APIRouter()


@router.get("/observations", response_model=ApiListResponse[OceanObservationResponse])
async def list_ocean_observations(
    dataset_id: Optional[str] = Query(None),
    station_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    depth_min: Optional[float] = Query(None),
    depth_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Returns oceanographic observations with spatial, temporal, and depth filters.
    """
    observations, total = OceanService.list_observations(
        dataset_id=dataset_id,
        station_id=station_id,
        date_from=date_from,
        date_to=date_to,
        depth_min=depth_min,
        depth_max=depth_max,
        page=page,
        page_size=page_size
    )
    return ApiListResponse(
        data=observations,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/observations/{observation_id}", response_model=ApiResponse[OceanObservationResponse])
async def get_ocean_observation(observation_id: str):
    """
    Retrieves a single ocean observation by ID.
    """
    obs = OceanService.get_observation_by_id(observation_id)
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OBSERVATION_NOT_FOUND", "message": f"Ocean observation '{observation_id}' not found."}
        )
    return ApiResponse(data=obs)


@router.get("/summary", response_model=ApiResponse[OceanSummaryResponse])
async def get_ocean_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """
    Returns aggregate oceanographic statistics (min, max, avg for temperature, salinity, DO, depth).
    """
    summary = OceanService.get_ocean_summary(date_from=date_from, date_to=date_to)
    return ApiResponse(data=summary)


@router.get("/trends", response_model=ApiResponse[OceanTrendResponse])
async def get_ocean_trends(
    variable: str = Query("temperature"),
    interval: str = Query("month"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """
    Returns time-series aggregated trends for oceanographic variables.
    """
    trends = OceanService.get_ocean_trends(
        variable=variable,
        interval=interval,
        date_from=date_from,
        date_to=date_to
    )
    return ApiResponse(data=trends)
