"""
Authentication Router: Wraps Supabase Auth GoTrue endpoints.
"""

from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from backend.app.auth.supabase_auth import get_current_user, security
from backend.app.config import settings
from backend.app.db.database import execute_single
from backend.app.db.queries import GET_PROFILE_BY_ID
from backend.app.schemas.auth import LoginRequest, LoginResponse, UserProfile, UserRole
from backend.app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/me", response_model=ApiResponse[UserProfile])
async def get_my_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and resolved role.
    """
    return ApiResponse(data=current_user)


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(req: LoginRequest):
    """
    Authenticates a user using Supabase Auth (email + password).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        if settings.ENVIRONMENT == "development":
            # Development-only fallback
            mock_id = "00000000-0000-0000-0000-000000000001"
            db_profile = None
            try:
                db_profile = execute_single(GET_PROFILE_BY_ID, {"user_id": mock_id})
            except Exception:
                pass

            resolved_role = UserRole.USER
            if db_profile and db_profile.get("role") == "admin":
                resolved_role = UserRole.ADMIN

            return ApiResponse(
                data=LoginResponse(
                    access_token="dev-mock-jwt-token-authenticated",
                    token_type="bearer",
                    user=UserProfile(
                        id=mock_id,
                        email=req.email,
                        full_name=db_profile.get("full_name") if db_profile else "Dev User",
                        role=resolved_role
                    )
                )
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "AUTH_SERVICE_UNCONFIGURED", "message": "Supabase Auth service is not configured."}
        )

    auth_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "email": req.email,
        "password": req.password
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(auth_url, json=payload, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "AUTH_SERVICE_ERROR", "message": f"Failed to contact authentication service: {str(e)}"}
        )

    if resp.status_code != 200:
        try:
            err_data = resp.json()
        except (ValueError, Exception):
            err_data = {}
        error_msg = err_data.get("error_description") or err_data.get("msg") or "Invalid email or password."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": error_msg}
        )

    try:
        data = resp.json()
    except (ValueError, Exception):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "INVALID_AUTH_RESPONSE", "message": "Non-JSON response received from upstream authentication service."}
        )

    access_token = data.get("access_token")
    user_data = data.get("user")
    if not access_token or not user_data or "id" not in user_data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "INVALID_AUTH_RESPONSE", "message": "Incomplete response from upstream authentication service."}
        )

    user_id = str(user_data["id"])
    
    # Populate role from database profile
    db_profile = None
    try:
        db_profile = execute_single(GET_PROFILE_BY_ID, {"user_id": user_id})
    except Exception:
        pass

    resolved_role = UserRole.ADMIN if db_profile and db_profile.get("role") == "admin" else UserRole.USER

    return ApiResponse(
        data=LoginResponse(
            access_token=access_token,
            token_type=data.get("token_type", "bearer"),
            user=UserProfile(
                id=user_id,
                email=user_data.get("email"),
                full_name=db_profile.get("full_name") if db_profile else user_data.get("user_metadata", {}).get("full_name"),
                role=resolved_role,
                department=db_profile.get("department") if db_profile else None,
                designation=db_profile.get("designation") if db_profile else None,
                created_at=str(db_profile.get("created_at")) if db_profile and db_profile.get("created_at") else None,
                updated_at=str(db_profile.get("updated_at")) if db_profile and db_profile.get("updated_at") else None
            )
        )
    )


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Revokes the active user session in Supabase Auth.
    """
    if credentials and credentials.credentials and settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        logout_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/logout"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {credentials.credentials}"
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(logout_url, headers=headers)
        except Exception:
            pass  # Session teardown is best-effort

    return ApiResponse(data={"message": "Logged out successfully."})
