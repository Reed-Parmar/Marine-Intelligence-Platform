"""
Datasets Router: CRUD, quality assessment, and provenance metadata.
Requires authenticated user and enforces ownership authorization on mutations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.auth.supabase_auth import get_current_user, get_optional_user
from backend.app.schemas.auth import UserProfile, UserRole
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.dataset import (
    DatasetCreateRequest,
    DatasetPreviewResponse,
    DatasetProvenanceResponse,
    DatasetQualityResponse,
    DatasetResponse,
    DatasetUpdateRequest
)
from backend.app.services.dataset_service import DatasetService

router = APIRouter()


@router.get("", response_model=ApiListResponse[DatasetResponse])
async def list_datasets(
    domain_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    quality_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Lists datasets with optional domain and quality filtering.
    """
    datasets, total = DatasetService.list_datasets(
        domain_type=domain_type,
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
async def get_dataset(
    dataset_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
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
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Registers a new dataset record.
    """
    ds = DatasetService.create_dataset(req, user_id=current_user.id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "DATASET_CREATE_FAILED", "message": "Failed to register dataset."}
        )
    return ApiResponse(data=ds)


@router.patch("/{dataset_id}", response_model=ApiResponse[DatasetResponse])
async def update_dataset(
    dataset_id: str,
    req: DatasetUpdateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Updates editable dataset metadata. Enforces ownership or admin role.
    """
    existing = DatasetService.get_dataset_by_id(dataset_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )

    if current_user.role != UserRole.ADMIN and existing.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "You do not have permission to modify this dataset."}
        )

    updated = DatasetService.update_dataset(dataset_id, req)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "DATASET_UPDATE_FAILED", "message": "Failed to update dataset."}
        )
    return ApiResponse(data=updated)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Deletes a dataset record. Enforces ownership or admin role.
    """
    existing = DatasetService.get_dataset_by_id(dataset_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )

    if current_user.role != UserRole.ADMIN and existing.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "You do not have permission to delete this dataset."}
        )

    success = DatasetService.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "DATASET_DELETE_FAILED", "message": "Failed to delete dataset."}
        )


@router.get("/{dataset_id}/quality", response_model=ApiResponse[DatasetQualityResponse])
async def get_dataset_quality(
    dataset_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Retrieves data quality evaluation report.
    """
    qc = DatasetService.get_dataset_quality(dataset_id)
    if not qc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )
    return ApiResponse(data=qc)


@router.get("/{dataset_id}/provenance", response_model=ApiResponse[DatasetProvenanceResponse])
async def get_dataset_provenance(
    dataset_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Retrieves dataset origin and processing audit logs.
    """
    prov = DatasetService.get_dataset_provenance(dataset_id)
    if not prov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )
    return ApiResponse(data=prov)


@router.get("/{dataset_id}/preview", response_model=ApiResponse[DatasetPreviewResponse])
async def get_dataset_preview(
    dataset_id: str,
    user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Retrieves tabular preview data for a registered dataset.
    """
    prev = DatasetService.get_dataset_preview(dataset_id)
    if not prev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset '{dataset_id}' not found."}
        )
    return ApiResponse(data=prev)
