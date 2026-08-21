"""
Alerts Router: Environmental anomalies and threshold notifications.
Queries real public.alerts table via SQLAlchemy.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.db.database import execute_query, execute_single, execute_write
from backend.app.schemas.alerts import AlertResponse, AlertSummaryResponse
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse

router = APIRouter()


@router.get("", response_model=ApiListResponse[AlertResponse])
async def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lists environmental and biological alerts from public.alerts.
    """
    conditions = []
    params: Dict[str, Any] = {}
    if status_filter:
        conditions.append("status = :status")
        params["status"] = status_filter
    if severity:
        conditions.append("severity = :severity")
        params["severity"] = severity
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    count_res = execute_single(f"SELECT COUNT(*) as total FROM public.alerts {where_clause};", params)
    total = count_res["total"] if count_res else 0

    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset
    rows = execute_query(
        f"SELECT * FROM public.alerts {where_clause} ORDER BY created_at DESC LIMIT :limit OFFSET :offset;",
        params
    )
    alerts = [
        AlertResponse(
            id=str(r["id"]),
            alert_type=r["alert_type"],
            severity=r["severity"],
            title=r["title"],
            message=r["message"],
            status=r.get("status", "active"),
            latitude=float(r["latitude"]) if r.get("latitude") is not None else None,
            longitude=float(r["longitude"]) if r.get("longitude") is not None else None,
            created_at=str(r["created_at"]) if r.get("created_at") else None
        )
        for r in rows
    ]
    return ApiListResponse(
        data=alerts,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/summary", response_model=ApiResponse[AlertSummaryResponse])
async def get_alerts_summary():
    """
    Returns aggregate alert counts by severity and alert type from public.alerts.
    """
    summary_query = """
    SELECT 
        COUNT(*) as total_alerts,
        COUNT(*) FILTER (WHERE status = 'active') as active_count,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
        COUNT(*) FILTER (WHERE severity = 'warning') as warning_count,
        COUNT(*) FILTER (WHERE severity = 'info') as info_count
    FROM public.alerts;
    """
    type_query = """
    SELECT alert_type, COUNT(*) as count
    FROM public.alerts
    GROUP BY alert_type;
    """
    r = execute_single(summary_query)
    type_rows = execute_query(type_query)
    alerts_by_type = {str(row["alert_type"]): int(row["count"]) for row in type_rows if row.get("alert_type")}

    if not r:
        return ApiResponse(
            data=AlertSummaryResponse(
                total_alerts=0,
                active_count=0,
                critical_count=0,
                warning_count=0,
                info_count=0,
                alerts_by_type={}
            )
        )

    return ApiResponse(
        data=AlertSummaryResponse(
            total_alerts=r.get("total_alerts", 0),
            active_count=r.get("active_count", 0),
            critical_count=r.get("critical_count", 0),
            warning_count=r.get("warning_count", 0),
            info_count=r.get("info_count", 0),
            alerts_by_type=alerts_by_type
        )
    )


@router.patch("/{alert_id}", response_model=ApiResponse[AlertResponse])
async def update_alert(alert_id: str, status_val: str = Query("acknowledged", alias="status")):
    """
    Acknowledges or resolves an alert in public.alerts.
    Only 'acknowledged' and 'resolved' are permitted status transitions.
    """
    valid_statuses = {"acknowledged", "resolved"}
    if status_val not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ALERT_STATUS", "message": f"Status must be one of: {', '.join(sorted(valid_statuses))}"}
        )

    query = """
    UPDATE public.alerts
    SET status = :status
    WHERE id = :alert_id
    RETURNING *;
    """
    r = execute_write(query, {"status": status_val, "alert_id": alert_id})
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' not found."}
        )
    return ApiResponse(
        data=AlertResponse(
            id=str(r["id"]),
            alert_type=r["alert_type"],
            severity=r["severity"],
            title=r["title"],
            message=r["message"],
            status=r.get("status", "active"),
            latitude=float(r["latitude"]) if r.get("latitude") is not None else None,
            longitude=float(r["longitude"]) if r.get("longitude") is not None else None,
            created_at=str(r["created_at"]) if r.get("created_at") else None
        )
    )
