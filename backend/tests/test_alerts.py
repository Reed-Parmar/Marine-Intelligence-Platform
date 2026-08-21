"""
Test Alerts endpoints: list, summary grouping, status update validation.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_alerts_summary(monkeypatch):
    """GET /api/v1/alerts/summary returns counts and alerts_by_type."""
    from backend.app.api.v1 import alerts

    monkeypatch.setattr(alerts, "execute_single", lambda q, p=None: {
        "total_alerts": 5,
        "active_count": 3,
        "critical_count": 1,
        "warning_count": 2,
        "info_count": 0
    })
    monkeypatch.setattr(alerts, "execute_query", lambda q, p=None: [
        {"alert_type": "marine_heatwave", "count": 3},
        {"alert_type": "hypoxia", "count": 2}
    ])

    response = client.get("/api/v1/alerts/summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_alerts"] == 5
    assert data["active_count"] == 3
    assert data["alerts_by_type"] == {"marine_heatwave": 3, "hypoxia": 2}


def test_update_alert_invalid_status():
    """PATCH /api/v1/alerts/{id} rejects invalid status transitions."""
    response = client.patch(
        "/api/v1/alerts/alert-001?status=invalid_status"
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_ALERT_STATUS"
