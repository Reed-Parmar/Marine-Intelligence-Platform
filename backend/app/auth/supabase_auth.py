"""
Supabase JWT Authentication Dependency.
Verifies Supabase Bearer tokens and loads the user profile & role from PostgreSQL via SQLAlchemy.
"""

import logging
from typing import Any, Dict, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.config import settings
from backend.app.db.database import execute_single
from backend.app.db.queries import GET_PROFILE_BY_ID
from backend.app.schemas.auth import UserProfile, UserRole

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str:
    return (
        settings.SUPABASE_JWT_SECRET
        or settings.SUPABASE_SERVICE_ROLE_KEY
        or ("cmlre-development-fallback-secret-key-32chars" if settings.ENVIRONMENT == "development" else "")
    )


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a Supabase JWT.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "Authorization token required."}
        )

    secret = _get_jwt_secret()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "JWT_SECRET_MISSING", "message": "Server authentication secret is not configured."}
        )

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "JWT token has expired."}
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
    Returns the authenticated UserProfile with role resolved from the database.
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
            detail={"code": "INVALID_TOKEN", "message": "Token missing user identifier (sub)."}
        )

    # Fetch profile from DB using SQLAlchemy
    try:
        profile = execute_single(GET_PROFILE_BY_ID, {"user_id": user_id})
    except Exception:
        profile = None

    if profile:
        db_role = str(profile.get("role", "user")).lower()
        resolved_role = UserRole.ADMIN if db_role == "admin" else UserRole.USER
        return UserProfile(
            id=str(profile["id"]),
            email=profile.get("email") or payload.get("email"),
            full_name=profile.get("full_name") or payload.get("user_metadata", {}).get("full_name"),
            role=resolved_role,
            institution=profile.get("institution"),
            department=profile.get("department"),
            designation=profile.get("designation"),
            created_at=str(profile.get("created_at")) if profile.get("created_at") else None,
            updated_at=str(profile.get("updated_at")) if profile.get("updated_at") else None
        )

    # Claims-based fallback: strictly assign default "user" role, never granting admin from token metadata
    user_meta = payload.get("user_metadata", {})
    return UserProfile(
        id=str(user_id),
        email=payload.get("email"),
        full_name=user_meta.get("full_name") or payload.get("email"),
        role=UserRole.USER
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
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin privileges required for this action."}
        )
    return current_user
