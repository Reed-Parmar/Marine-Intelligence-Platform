"""
Auth Router: Login, session, and current user profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.auth.supabase_auth import get_current_user
from backend.app.config import settings
from backend.app.schemas.auth import LoginRequest, LoginResponse, UserProfile
from backend.app.schemas.common import ApiResponse
import httpx

router = APIRouter()


@router.get("/me", response_model=ApiResponse[UserProfile])
async def get_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile, role, and department.
    """
    return ApiResponse(data=current_user)


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(req: LoginRequest):
    """
    Authenticates user directly via Supabase Auth /token endpoint.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        # Development fallback response for testing
        dev_user = UserProfile(
            id="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            email=req.email,
            full_name="CMLRE Researcher",
            role="admin" if "admin" in req.email else "user"
        )
        return ApiResponse(
            data=LoginResponse(
                access_token="dev-mock-jwt-token",
                user=dev_user
            )
        )

    # Supabase GoTrue Auth password grant
    auth_url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "email": req.email,
        "password": req.password
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(auth_url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code != 200:
                err_data = resp.json() if resp.content else {}
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "INVALID_CREDENTIALS", "message": err_data.get("msg") or "Invalid email or password."}
                )
            
            data = resp.json()
            user_data = data.get("user", {})
            user_profile = UserProfile(
                id=user_data.get("id"),
                email=user_data.get("email"),
                full_name=user_data.get("user_metadata", {}).get("full_name") or user_data.get("email"),
                role=user_data.get("role") or user_data.get("user_metadata", {}).get("role", "user")
            )
            return ApiResponse(
                data=LoginResponse(
                    access_token=data.get("access_token"),
                    user=user_profile
                )
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "AUTH_SERVICE_UNAVAILABLE", "message": f"Authentication provider unavailable: {str(e)}"}
            )


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(current_user: UserProfile = Depends(get_current_user)):
    """
    Logs out the current session.
    """
    return ApiResponse(data={"status": "logged_out", "user_id": current_user.id})
