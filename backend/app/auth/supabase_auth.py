"""
Supabase JWT Authentication Dependency.
Verifies Supabase Bearer tokens and loads the user profile & role from PostgreSQL via SQLAlchemy.
"""

from typing import Any, Dict, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.config import settings
from backend.app.db.database import execute_single
from backend.app.db.queries import GET_PROFILE_BY_ID
from backend.app.schemas.auth import UserProfile

security = HTTPBearer(auto_error=False)


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a Supabase JWT.
    Uses SUPABASE_JWT_SECRET if provided, otherwise decodes payload in development mode.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "Authorization token required"}
        )

    try:
        # If secret is provided, verify signature
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        else:
            # Development fallback: decode claims and validate expiration
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": True}
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "JWT token has expired"}
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": f"Invalid JWT token: {str(e)}"}
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserProfile:
    """
    FastAPI dependency that enforces authentication.
    Returns the authenticated UserProfile with role.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required. Provide Bearer token."}
        )

    payload = decode_supabase_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token missing user identifier (sub)"}
        )

    # Fetch profile from DB using SQLAlchemy
    profile = execute_single(GET_PROFILE_BY_ID, {"user_id": user_id})
    if profile:
        return UserProfile(
            id=str(profile["id"]),
            email=profile.get("email") or payload.get("email"),
            full_name=profile.get("full_name") or payload.get("user_metadata", {}).get("full_name"),
            role=profile.get("role", "user"),
            department=profile.get("department"),
            designation=profile.get("designation"),
            created_at=str(profile.get("created_at")) if profile.get("created_at") else None,
            updated_at=str(profile.get("updated_at")) if profile.get("updated_at") else None
        )

    # If profile record not yet in public.profiles, construct from token claims
    user_meta = payload.get("user_metadata", {})
    return UserProfile(
        id=str(user_id),
        email=payload.get("email"),
        full_name=user_meta.get("full_name") or payload.get("email"),
        role=payload.get("role") or user_meta.get("role") or "user"
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserProfile]:
    """Optional authentication dependency; returns None if not authenticated."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_admin(
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfile:
    """Dependency that enforces admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin privileges required for this action."}
        )
    return current_user
