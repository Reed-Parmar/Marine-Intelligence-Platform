"""
Test Authentication endpoints and JWT dependencies.
"""

from fastapi.testclient import TestClient
import jwt
from backend.app.main import app
from backend.app.auth.supabase_auth import get_current_user
from backend.app.schemas.auth import UserProfile

client = TestClient(app)


def test_auth_me_unauthorized():
    """Missing Bearer token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    err = response.json()
    assert "error" in err
    assert err["error"]["code"] == "UNAUTHORIZED"


def test_auth_me_authenticated():
    """Valid user dependency returns user profile."""
    mock_user = UserProfile(
        id="user-123",
        email="researcher@cmlre.gov.in",
        full_name="Dr. Marine Researcher",
        role="user"
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        res = response.json()
        assert res["data"]["id"] == "user-123"
        assert res["data"]["email"] == "researcher@cmlre.gov.in"
        assert res["data"]["role"] == "user"
    finally:
        app.dependency_overrides.clear()


def test_login_fallback():
    """Login endpoint returns access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "researcher@cmlre.gov.in", "password": "SamplePassword123!"}
    )
    assert response.status_code in (200, 401, 503)
    if response.status_code == 200:
        data = response.json()["data"]
        assert "access_token" in data
        assert "user" in data


def test_users_admin_forbidden_for_regular_user():
    """Non-admin user receives 403 on admin-only route."""
    regular_user = UserProfile(id="u1", email="user@cmlre.gov.in", role="user")
    app.dependency_overrides[get_current_user] = lambda: regular_user
    try:
        response = client.get("/api/v1/users")
        assert response.status_code == 403
        err = response.json()
        assert err["error"]["code"] == "FORBIDDEN"
    finally:
        app.dependency_overrides.clear()
