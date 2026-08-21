"""
Authentication Router: Wraps Supabase Auth GoTrue endpoints with profile persistence and registration.
"""

import json
import logging
import time
import uuid
from typing import Optional
import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from backend.app.auth.supabase_auth import get_current_user, security
from backend.app.config import settings
from backend.app.db.database import execute_single, execute_write
from backend.app.db.queries import GET_PROFILE_BY_ID
from backend.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserProfile,
    UserRole
)
from backend.app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def create_access_token(user_id: str, email: str, role: str = "authenticated") -> str:
    """Creates a standard signed Supabase-compatible JWT token."""
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "JWT_SECRET_MISSING", "message": "Server authentication secret is not configured."}
        )
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "aud": "authenticated",
        "iss": "supabase",
        "exp": int(time.time()) + 86400 * 7,
        "iat": int(time.time())
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@router.get("/me", response_model=ApiResponse[UserProfile])
async def get_my_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and resolved role.
    """
    return ApiResponse(data=current_user)


@router.post("/register", response_model=ApiResponse[LoginResponse])
@router.post("/signup", response_model=ApiResponse[LoginResponse])
async def register(req: RegisterRequest):
    """
    Registers a new scientific researcher and provisions their database profile and session.
    Directly provisions auth credentials to bypass Supabase built-in SMTP email rate limits
    while ensuring seamless JWT session issuance.
    """
    user_id = str(uuid.uuid4())
    identity_id = str(uuid.uuid4())

    # Check if user with this email already exists
    try:
        existing_user = execute_single(
            "SELECT id FROM auth.users WHERE LOWER(email) = LOWER(:email)",
            {"email": req.email}
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "USER_ALREADY_EXISTS", "message": "A researcher with this institutional email is already registered."}
            )
    except HTTPException:
        raise
    except Exception as err:
        logger.error("Database error while checking existing user: %s", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "DATABASE_ERROR", "message": "Failed to verify registration eligibility."}
        )

    # 1. Provision user directly in auth.users and auth.identities
    # Server-controlled role default: 'user'
    provisioned_direct = False
    last_error = None
    try:
        user_metadata = {
            "full_name": req.full_name,
            "institution": req.institution or "CMLRE, Kochi",
            "department": req.department,
            "designation": req.designation,
            "role": "user"
        }
        app_metadata = {
            "provider": "email",
            "providers": ["email"]
        }

        execute_write("""
            INSERT INTO auth.users (
                id, email, encrypted_password, email_confirmed_at,
                raw_app_meta_data, raw_user_meta_data, created_at, updated_at, role, aud
            )
            VALUES (
                :id::uuid,
                :email,
                extensions.crypt(:password, extensions.gen_salt('bf')),
                NOW(),
                CAST(:app_meta AS jsonb),
                CAST(:user_meta AS jsonb),
                NOW(),
                NOW(),
                'authenticated',
                'authenticated'
            );
        """, {
            "id": user_id,
            "email": req.email,
            "password": req.password,
            "app_meta": json.dumps(app_metadata),
            "user_meta": json.dumps(user_metadata)
        })

        execute_write("""
            INSERT INTO auth.identities (
                id, provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at
            )
            VALUES (
                :identity_id::uuid,
                :user_id,
                :user_id::uuid,
                jsonb_build_object('sub', :user_id, 'email', :email, 'full_name', :full_name),
                'email',
                NOW(),
                NOW(),
                NOW()
            );
        """, {
            "identity_id": identity_id,
            "user_id": user_id,
            "email": req.email,
            "full_name": req.full_name
        })

        execute_write("""
            INSERT INTO public.profiles (id, email, full_name, role, institution, department, designation)
            VALUES (:user_id, :email, :full_name, 'user'::public.user_role, :institution, :department, :designation)
            ON CONFLICT (id) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                email = EXCLUDED.email,
                institution = COALESCE(EXCLUDED.institution, public.profiles.institution),
                department = COALESCE(EXCLUDED.department, public.profiles.department),
                designation = COALESCE(EXCLUDED.designation, public.profiles.designation),
                updated_at = NOW();
        """, {
            "user_id": user_id,
            "email": req.email,
            "full_name": req.full_name,
            "institution": req.institution,
            "department": req.department,
            "designation": req.designation
        })
        provisioned_direct = True
    except Exception as db_err:
        last_error = db_err
        logger.error("Direct database provisioning failed: %s", db_err)
        # Fallback to Supabase GoTrue signup if direct DB write is unavailable
        if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            signup_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/signup"
            headers = {
                "apikey": settings.SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }
            signup_payload = {
                "email": req.email,
                "password": req.password,
                "data": {
                    "full_name": req.full_name,
                    "institution": req.institution,
                    "department": req.department,
                    "designation": req.designation,
                    "role": "user"
                }
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(signup_url, json=signup_payload, headers=headers)
                if resp.status_code in (200, 201):
                    user_data = resp.json()
                    user_id = str(user_data.get("id") or user_data.get("user", {}).get("id") or user_id)
                    provisioned_direct = True
            except Exception as http_err:
                logger.error("Supabase GoTrue signup fallback failed: %s", http_err)

    if not provisioned_direct:
        logger.error("User account provisioning failed completely: %s", last_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROVISIONING_FAILED", "message": "Failed to provision researcher account."}
        )

    # 2. Acquire authenticated JWT session via Supabase Token endpoint or generate valid signed JWT
    access_token = create_access_token(user_id=user_id, email=req.email, role="authenticated")
    token_type = "bearer"
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        token_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
        token_payload = {
            "email": req.email,
            "password": req.password
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                token_resp = await client.post(token_url, json=token_payload, headers=headers)
            if token_resp.status_code == 200:
                token_data = token_resp.json()
                if token_data.get("access_token"):
                    access_token = token_data.get("access_token")
                token_type = token_data.get("token_type", "bearer")
        except Exception as t_err:
            logger.warning("Could not obtain upstream token, using generated token: %s", t_err)

    # 3. Fetch resolved database profile
    db_profile = None
    try:
        db_profile = execute_single(GET_PROFILE_BY_ID, {"user_id": user_id})
    except Exception:
        pass

    resolved_role = UserRole.ADMIN if db_profile and db_profile.get("role") == "admin" else UserRole.USER

    return ApiResponse(
        data=LoginResponse(
            access_token=access_token,
            token_type=token_type,
            user=UserProfile(
                id=user_id,
                email=req.email,
                full_name=db_profile.get("full_name") if db_profile else req.full_name,
                role=resolved_role,
                institution=db_profile.get("institution") if db_profile else req.institution,
                department=db_profile.get("department") if db_profile else req.department,
                designation=db_profile.get("designation") if db_profile else req.designation,
                created_at=str(db_profile.get("created_at")) if db_profile and db_profile.get("created_at") else None,
                updated_at=str(db_profile.get("updated_at")) if db_profile and db_profile.get("updated_at") else None
            )
        )
    )


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(req: LoginRequest):
    """
    Authenticates a user using Supabase Auth (email + password).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        # In unconfigured-Supabase environment, verify password against stored password hash
        db_auth = execute_single("""
            SELECT u.id, p.email, p.full_name, p.role, p.institution, p.department, p.designation, p.created_at, p.updated_at
            FROM auth.users u
            JOIN public.profiles p ON u.id = p.id
            WHERE LOWER(u.email) = LOWER(:email)
              AND u.encrypted_password = extensions.crypt(:password, u.encrypted_password);
        """, {"email": req.email, "password": req.password})

        if db_auth:
            user_id = str(db_auth["id"])
            resolved_role = UserRole.ADMIN if db_auth.get("role") == "admin" else UserRole.USER
            access_token = create_access_token(user_id=user_id, email=db_auth["email"], role=db_auth.get("role", "authenticated"))
            return ApiResponse(
                data=LoginResponse(
                    access_token=access_token,
                    token_type="bearer",
                    user=UserProfile(
                        id=user_id,
                        email=db_auth["email"],
                        full_name=db_auth.get("full_name"),
                        role=resolved_role,
                        institution=db_auth.get("institution", "CMLRE"),
                        department=db_auth.get("department"),
                        designation=db_auth.get("designation"),
                        created_at=str(db_auth.get("created_at")) if db_auth.get("created_at") else None,
                        updated_at=str(db_auth.get("updated_at")) if db_auth.get("updated_at") else None
                    )
                )
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}
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
        logger.error("Upstream authentication service request failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "UPSTREAM_AUTH_UNAVAILABLE", "message": "Authentication service is currently unavailable."}
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}
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
                institution=db_profile.get("institution") if db_profile else user_data.get("user_metadata", {}).get("institution", "CMLRE"),
                department=db_profile.get("department") if db_profile else user_data.get("user_metadata", {}).get("department"),
                designation=db_profile.get("designation") if db_profile else user_data.get("user_metadata", {}).get("designation"),
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
