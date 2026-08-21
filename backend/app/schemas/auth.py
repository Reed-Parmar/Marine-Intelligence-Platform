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
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password for account (min 8 characters)")
    full_name: str = Field(..., min_length=1, description="Full name of researcher")
    institution: Optional[str] = Field(default=None, description="Research institution name")
    department: Optional[str] = Field(default=None, description="Department / Research Division")
    designation: Optional[str] = Field(default=None, description="Designation / Scientific Role")


class RoleUpdateRequest(BaseModel):
    role: UserRole
