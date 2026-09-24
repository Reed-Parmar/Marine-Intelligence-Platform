"""
Test CORS configuration and security.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_cors_allowed_origin():
    """Requests with trusted Origin header receive Access-Control-Allow-Origin."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_untrusted_origin():
    """Requests from untrusted origins are not permitted credentialed CORS headers."""
    response = client.get(
        "/health",
        headers={"Origin": "http://untrusted-site.com"}
    )
    assert response.status_code == 200
    # Access-Control-Allow-Origin header is omitted for untrusted origins
    assert response.headers.get("access-control-allow-origin") is None
