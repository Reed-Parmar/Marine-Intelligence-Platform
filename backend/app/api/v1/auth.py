"""
Authentication Router: Provides authenticated profile querying and updates.
User authentication, registration, password hashing, and token issuance are handled directly by Supabase Auth.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.auth.supabase_auth import get_current_user
from backend.app.db.database import execute_single, execute_write
from backend.app.db.queries import GET_PROFILE_BY_ID
from backend.app.schemas.auth import UserProfile, UserRole
from backend.app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, description="Researcher full name")
    institution: Optional[str] = Field(None, description="Research institute / affiliation")
    department: Optional[str] = Field(None, description="Division / Department")
    designation: Optional[str] = Field(None, description="Scientific role / designation")


@router.get("/me", response_model=ApiResponse[UserProfile])
async def get_my_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and resolved role from PostgreSQL.
    Requires a valid Supabase access token in the Authorization Bearer header.
    """
    return ApiResponse(data=current_user)


@router.put("/profile", response_model=ApiResponse[UserProfile])
async def update_my_profile(
    req: ProfileUpdateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Updates the authenticated researcher's application profile in public.profiles.
    """
    try:
        execute_write("""
            INSERT INTO public.profiles (id, email, full_name, institution, department, designation, role)
            VALUES (:id, :email, :full_name, :institution, :department, :designation, :role::public.user_role)
            ON CONFLICT (id) DO UPDATE
            SET full_name = COALESCE(:full_name, public.profiles.full_name),
                institution = COALESCE(:institution, public.profiles.institution),
                department = COALESCE(:department, public.profiles.department),
                designation = COALESCE(:designation, public.profiles.designation),
                updated_at = NOW();
        """, {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": req.full_name or current_user.full_name,
            "institution": req.institution or current_user.institution,
            "department": req.department or current_user.department,
            "designation": req.designation or current_user.designation,
            "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        })

        updated = execute_single(GET_PROFILE_BY_ID, {"user_id": current_user.id})
        if not updated:
            return ApiResponse(data=current_user)

        db_role = str(updated.get("role", "user")).lower()
        resolved_role = UserRole.ADMIN if db_role == "admin" else UserRole.USER

        return ApiResponse(
            data=UserProfile(
                id=str(updated["id"]),
                email=updated.get("email") or current_user.email,
                full_name=updated.get("full_name") or current_user.full_name,
                role=resolved_role,
                institution=updated.get("institution"),
                department=updated.get("department"),
                designation=updated.get("designation"),
                created_at=str(updated.get("created_at")) if updated.get("created_at") else None,
                updated_at=str(updated.get("updated_at")) if updated.get("updated_at") else None
            )
        )
    except Exception as e:
        logger.error("Failed to update researcher profile: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROFILE_UPDATE_FAILED", "message": "Failed to update researcher profile."}
        )

