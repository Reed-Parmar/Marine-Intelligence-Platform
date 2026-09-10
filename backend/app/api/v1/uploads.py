"""
Uploads Router: File staging, preview parsing, and Phase 3/4 pipeline processing hook.
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from backend.app.auth.supabase_auth import get_optional_user
from backend.app.schemas.auth import UserProfile
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.upload import (
    UploadPreviewResponse,
    UploadProcessRequest,
    UploadProcessResponse,
    UploadResponse
)
from backend.app.services.upload_service import UploadService

router = APIRouter()


@router.post("", response_model=ApiResponse[UploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Uploads and stages a dataset file for format detection and preview.
    """
    res = await UploadService.create_upload(file, user_id=user.id if user else None)
    return ApiResponse(data=res)


@router.get("/{upload_id}", response_model=ApiResponse[UploadResponse])
def get_upload_status(upload_id: str):
    """
    Returns upload status and detected format.
    """
    res = UploadService.get_upload_status(upload_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "UPLOAD_NOT_FOUND", "message": "Upload session not found."}
        )
    return ApiResponse(data=res)


@router.get("/{upload_id}/preview", response_model=ApiResponse[UploadPreviewResponse])
def get_upload_preview(upload_id: str):
    """
    Parses and returns a tabular preview of the staged dataset for frontend inspection.
    """
    preview = UploadService.get_upload_preview(upload_id)
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "UPLOAD_NOT_FOUND", "message": "Upload session not found for preview."}
        )
    return ApiResponse(data=preview)


@router.post("/{upload_id}/process", response_model=ApiResponse[UploadProcessResponse])
def process_upload(
    upload_id: str,
    req: UploadProcessRequest,
    user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Invokes ingestion parsing and Phase 4 Quality Pipeline, then registers the finalized dataset.
    """
    res = UploadService.process_upload(upload_id, req, user_id=user.id if user else None)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "UPLOAD_NOT_FOUND", "message": "Upload not found to process."}
        )
    return ApiResponse(data=res)


@router.delete("/{upload_id}", response_model=ApiResponse[dict])
def cancel_upload(upload_id: str):
    """
    Cancels and removes a staged upload.
    """
    success = UploadService.delete_upload(upload_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "UPLOAD_NOT_FOUND", "message": "Upload not found to cancel."}
        )
    return ApiResponse(data={"status": "deleted", "upload_id": upload_id})
