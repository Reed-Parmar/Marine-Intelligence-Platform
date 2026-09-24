"""
Common API response schemas matching the CMLRE Backend API Contract.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiMeta(BaseModel):
    page: Optional[int] = None
    page_size: Optional[int] = None
    total: Optional[int] = None
    timestamp: Optional[str] = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard success response wrapper for single objects: {"data": ..., "meta": ...}"""
    data: T
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ApiListResponse(BaseModel, Generic[T]):
    """Standard success response wrapper for list arrays: {"data": [...], "meta": {"page": 1, ...}}"""
    data: List[T]
    meta: ApiMeta


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response format: {"error": {"code": "...", "message": "..."}}"""
    error: ApiError
