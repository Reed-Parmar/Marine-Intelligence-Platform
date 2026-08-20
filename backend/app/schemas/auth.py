"""
Authentication and User schemas.
"""

from typing import Optional
from pydantic import BaseModel


class UserRole(str):
    ADMIN = "admin"
    USER = "user"


class UserProfile(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "user"
    department: Optional[str] = None
    designation: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class RoleUpdateRequest(BaseModel):
    role: str
