import io
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from PIL import Image

from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.species import (
    SpeciesDistributionResponse,
    SpeciesOccurrenceResponse,
    SpeciesResponse,
    SpeciesIdentificationResponse,
    SpeciesModelInfoResponse,
)
from backend.app.services.species_service import SpeciesService
from ml.species_identification import get_species_identifier

router = APIRouter()


@router.post(
    "/identify",
    response_model=SpeciesIdentificationResponse,
    summary="Identify marine fish species from uploaded image",
    description="Fine-tuned ResNet-18 Deep Learning classifier (Phase 14.2) for 10 reef & pelagic marine species."
)
async def identify_marine_species(
    file: UploadFile = File(..., description="Underwater photograph or camera frame (JPEG, PNG, WebP)"),
    top_k: int = Query(3, ge=1, le=10, description="Number of top candidates to return (1-10)")
):
    """
    Identifies marine fish species from an uploaded photograph or underwater video frame.
    Returns calibrated probability scores, confidence tier (HIGH/MODERATE/LOW), and taxonomic metadata.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "No file uploaded."}
        )

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    if ext and ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_IMAGE_FORMAT",
                "message": f"Unsupported file extension '{ext}'. Supported formats: {', '.join(sorted(allowed_exts))}."
            }
        )

    contents = await file.read()
    if not contents or len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "Uploaded image file is empty."}
        )

    # 20MB payload limit
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "FILE_TOO_LARGE", "message": "Uploaded image exceeds 20MB limit."}
        )

    try:
        # Validate that bytes represent an image
        with Image.open(io.BytesIO(contents)) as pil_img:
            pil_img.verify()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CORRUPT_IMAGE", "message": f"Uploaded file is not a valid image: {str(e)}"}
        )

    try:
        ident = get_species_identifier()
        result = ident.predict(contents, top_k=top_k)
        return SpeciesIdentificationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INFERENCE_ERROR", "message": f"Classification error: {str(e)}"}
        )


@router.get(
    "/health",
    summary="Verifies species classification model status",
    tags=["Species Identification"]
)
def species_health():
    """Verifies species classification model status and version."""
    ident = get_species_identifier()
    return {
        "status": "ready",
        "model": "MarineSpeciesClassifier-ResNet18",
        "version": ident.model_version,
        "classes": ident.num_classes
    }


@router.get(
    "/identify/model-info",
    response_model=SpeciesModelInfoResponse,
    summary="Get metadata and supported species catalog for the vision model"
)
async def get_species_model_info():
    """
    Returns full metadata, architecture, version, and the complete 10-species
    taxonomic catalogue supported by the fine-tuned ResNet-18 model.
    """
    ident = get_species_identifier()
    return SpeciesModelInfoResponse(**ident.get_model_info())


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
