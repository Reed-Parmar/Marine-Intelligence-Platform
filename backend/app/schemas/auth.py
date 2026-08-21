"""
Authentication and User schemas.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserProfile(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    institution: Optional[str] = None
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


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=1, description="Password for account")
    full_name: str = Field(..., min_length=1, description="Full name of researcher")
    institution: Optional[str] = Field(default="CMLRE, Kochi", description="Research institution name")
    department: Optional[str] = Field(default=None, description="Department / Research Division")
    designation: Optional[str] = Field(default=None, description="Designation / Scientific Role")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="User role")


class RoleUpdateRequest(BaseModel):
    role: UserRole
