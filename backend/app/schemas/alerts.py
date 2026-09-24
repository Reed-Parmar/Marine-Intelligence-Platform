"""
Alert Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str  # info, warning, critical
    title: str
    message: str
    status: str = "active"  # active, acknowledged, resolved
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[str] = None


class AlertSummaryResponse(BaseModel):
    total_alerts: int
    active_count: int
    critical_count: int
    warning_count: int
    info_count: int
    alerts_by_type: Dict[str, int] = Field(default_factory=dict)
