"""
Species Router: Taxonomy catalog, species profiles, occurrences, and spatial distribution.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.species import (
    SpeciesDistributionResponse,
    SpeciesOccurrenceResponse,
    SpeciesResponse
)
from backend.app.services.species_service import SpeciesService

router = APIRouter()


@router.get("", response_model=ApiListResponse[SpeciesResponse])
async def list_species(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Search and list marine species from the taxonomy catalog.
    """
    species_list, total = SpeciesService.search_species(
        search=search,
        page=page,
        page_size=page_size
    )
    return ApiListResponse(
        data=species_list,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/{species_id}", response_model=ApiResponse[SpeciesResponse])
async def get_species(species_id: str):
    """
    Retrieves full taxonomy and biological profile for a single species.
    """
    sp = SpeciesService.get_species_by_id(species_id)
    if not sp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SPECIES_NOT_FOUND", "message": f"Species '{species_id}' not found."}
        )
    return ApiResponse(data=sp)


@router.get("/{species_id}/occurrences", response_model=ApiListResponse[SpeciesOccurrenceResponse])
async def get_species_occurrences(
    species_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Returns spatial and temporal occurrences for a species.
    """
    occurrences, total = SpeciesService.get_species_occurrences(
        species_id=species_id,
        page=page,
        page_size=page_size
    )
    return ApiListResponse(
        data=occurrences,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/{species_id}/distribution", response_model=ApiResponse[SpeciesDistributionResponse])
async def get_species_distribution(species_id: str):
    """
    Returns spatial bounding box and depth distribution stats for map visualization.
    """
    dist = SpeciesService.get_species_distribution(species_id)
    if not dist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DISTRIBUTION_NOT_FOUND", "message": f"No distribution data for species '{species_id}'."}
        )
    return ApiResponse(data=dist)
