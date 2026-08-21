"""
Users Router: User profile management and admin role assignment.
Uses SQLAlchemy parameterized queries.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.auth.supabase_auth import get_current_user, require_admin
from backend.app.db.database import execute_query, execute_single, execute_write
from backend.app.db.queries import COUNT_ALL_PROFILES, GET_ALL_PROFILES, UPDATE_USER_ROLE
from backend.app.schemas.auth import RoleUpdateRequest, UserProfile
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse

router = APIRouter()


@router.get("/me", response_model=ApiResponse[UserProfile])
async def get_user_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the current user profile.
    """
    return ApiResponse(data=current_user)


@router.get("", response_model=ApiListResponse[UserProfile])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin: UserProfile = Depends(require_admin)
):
    """
    Admin-only: lists all registered user profiles.
    """
    offset = (page - 1) * page_size
    count_res = execute_single(COUNT_ALL_PROFILES)
    total = count_res["total"] if count_res else 0

    rows = execute_query(GET_ALL_PROFILES, {"limit": page_size, "offset": offset})
    users = [
        UserProfile(
            id=str(r["id"]),
            email=r.get("email"),
            full_name=r.get("full_name"),
            role=r.get("role", "user"),
            department=r.get("department"),
            designation=r.get("designation"),
            created_at=str(r["created_at"]) if r.get("created_at") else None,
            updated_at=str(r["updated_at"]) if r.get("updated_at") else None
        )
        for r in rows
    ]
    return ApiListResponse(
        data=users,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.patch("/{user_id}/role", response_model=ApiResponse[UserProfile])
async def update_user_role(
    user_id: str,
    req: RoleUpdateRequest,
    admin: UserProfile = Depends(require_admin)
):
    """
    Admin-only: Updates a user's platform role.
    """
    valid_roles = {"admin", "user", "researcher", "scientist", "viewer"}
    if req.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ROLE", "message": f"Role must be one of: {', '.join(sorted(valid_roles))}"}
        )

    r = execute_write(UPDATE_USER_ROLE, {"role": req.role, "user_id": user_id})
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found."}
        )

    updated_profile = UserProfile(
        id=str(r["id"]),
        email=r.get("email"),
        full_name=r.get("full_name"),
        role=r.get("role", "user"),
        department=r.get("department"),
        designation=r.get("designation"),
        updated_at=str(r["updated_at"]) if r.get("updated_at") else None
    )
    return ApiResponse(data=updated_profile)
