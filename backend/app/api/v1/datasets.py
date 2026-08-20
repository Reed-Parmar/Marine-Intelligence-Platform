"""
Datasets Router: Dataset registration, listing, retrieval, quality scores, and provenance.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.auth.supabase_auth import get_optional_user
from backend.app.schemas.auth import UserProfile
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.dataset import (
    DatasetCreateRequest,
    DatasetProvenanceResponse,
    DatasetQualityResponse,
    DatasetResponse,
    DatasetUpdateRequest
)
from backend.app.services.dataset_service import DatasetService

router = APIRouter()


@router.get("", response_model=ApiListResponse[DatasetResponse])
async def list_datasets(
    domain: Optional[str] = Query(None, alias="domain"),
    status: Optional[str] = Query(None),
    quality_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lists datasets with domain, status, and quality filters.
    """
    datasets, total = DatasetService.list_datasets(
        domain_type=domain,
        status=status,
        quality_status=quality_status,
        search=search,
        page=page,
        page_size=page_size
    )
    return ApiListResponse(
        data=datasets,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/{dataset_id}", response_model=ApiResponse[DatasetResponse])
async def get_dataset(dataset_id: str):
    """
    Retrieves full metadata for a single dataset.
    """
    ds = DatasetService.get_dataset_by_id(dataset_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )
    return ApiResponse(data=ds)


@router.post("", response_model=ApiResponse[DatasetResponse], status_code=status.HTTP_201_CREATED)
async def create_dataset(
    req: DatasetCreateRequest,
    user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Registers a new dataset.
    """
    ds = DatasetService.create_dataset(req, user_id=user.id if user else None)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DATASET_CREATION_FAILED", "message": "Failed to create dataset."}
        )
    return ApiResponse(data=ds)


@router.patch("/{dataset_id}", response_model=ApiResponse[DatasetResponse])
async def update_dataset(dataset_id: str, req: DatasetUpdateRequest):
    """
    Updates editable dataset metadata.
    """
    ds = DatasetService.update_dataset(dataset_id, req)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found to update."}
        )
    return ApiResponse(data=ds)


@router.delete("/{dataset_id}", response_model=ApiResponse[dict])
async def delete_dataset(dataset_id: str):
    """
    Deletes a dataset.
    """
    success = DatasetService.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found to delete."}
        )
    return ApiResponse(data={"status": "deleted", "dataset_id": dataset_id})


@router.get("/{dataset_id}/quality", response_model=ApiResponse[DatasetQualityResponse])
async def get_dataset_quality(dataset_id: str):
    """
    Returns data quality scores, status, and validation issues for a dataset.
    """
    res = DatasetService.get_dataset_quality(dataset_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )
    return ApiResponse(data=res)


@router.get("/{dataset_id}/provenance", response_model=ApiResponse[DatasetProvenanceResponse])
async def get_dataset_provenance(dataset_id: str):
    """
    Returns audit provenance metadata and transformation logs.
    """
    res = DatasetService.get_dataset_provenance(dataset_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )
    return ApiResponse(data=res)
