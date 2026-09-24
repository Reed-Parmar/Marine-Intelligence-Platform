"""
Fisheries Router: Catch logs, effort statistics, gear summaries, and catch trends.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.fisheries import (
    FisheriesObservationResponse,
    FisheriesSummaryResponse,
    FisheriesTrendResponse
)
from backend.app.services.fisheries_service import FisheriesService

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
