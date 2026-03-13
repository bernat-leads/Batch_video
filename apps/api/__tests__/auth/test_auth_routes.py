"""Tests for authentication routes and session cookie handling."""

import uuid

import pytest
from fastapi.testclient import TestClient

from api.app import create_application
from api.settings import settings

TEST_PASSWORD = "test-secret-password"
FAKE_VIDEO_ID = str(uuid.uuid4())
FAKE_SHOT_ID = str(uuid.uuid4())

PROTECTED_ROUTES = [
    ("GET", "/api/v1/videos/"),
    ("POST", "/api/v1/videos/"),
    ("GET", f"/api/v1/videos/{FAKE_VIDEO_ID}"),
    ("PATCH", f"/api/v1/videos/{FAKE_VIDEO_ID}"),
    ("DELETE", f"/api/v1/videos/{FAKE_VIDEO_ID}"),
    ("GET", f"/api/v1/videos/{FAKE_VIDEO_ID}/shots/"),
    ("POST", f"/api/v1/videos/{FAKE_VIDEO_ID}/shots/"),
    ("GET", f"/api/v1/videos/{FAKE_VIDEO_ID}/shots/{FAKE_SHOT_ID}"),
    ("PATCH", f"/api/v1/videos/{FAKE_VIDEO_ID}/shots/{FAKE_SHOT_ID}"),
    ("DELETE", f"/api/v1/videos/{FAKE_VIDEO_ID}/shots/{FAKE_SHOT_ID}"),
    ("GET", "/api/v1/auth/me"),
]

PUBLIC_ROUTES = [
    ("GET", "/"),
    ("GET", "/health"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
]


@pytest.fixture(autouse=True)
def _set_app_password(monkeypatch: pytest.MonkeyPatch):
    """Set APP_PASSWORD for all tests in this module."""
    monkeypatch.setattr(settings, "APP_PASSWORD", TEST_PASSWORD)


@pytest.fixture
def auth_client() -> TestClient:
    app = create_application()
    return TestClient(app)


class TestLogin:
    def test_login_success(self, auth_client: TestClient):
        response = auth_client.post(
            "/api/v1/auth/login", json={"password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        assert response.json() == {"authenticated": True}
        assert "session" in response.cookies

    def test_login_wrong_password(self, auth_client: TestClient):
        response = auth_client.post(
            "/api/v1/auth/login", json={"password": "wrong"}
        )
        assert response.status_code == 401
        assert "session" not in response.cookies


class TestMe:
    def test_me_with_valid_session(self, auth_client: TestClient):
        auth_client.post("/api/v1/auth/login", json={"password": TEST_PASSWORD})
        response = auth_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json() == {"authenticated": True}

    def test_me_without_cookie(self, auth_client: TestClient):
        response = auth_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_with_tampered_cookie(self, auth_client: TestClient):
        auth_client.cookies.set("session", "tampered-value")
        response = auth_client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestLogout:
    def test_logout_clears_cookie(self, auth_client: TestClient):
        auth_client.post("/api/v1/auth/login", json={"password": TEST_PASSWORD})
        response = auth_client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json() == {"authenticated": False}
        response = auth_client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestProtectedRoutes:
    """Every protected endpoint must return 401 without a session cookie."""

    @pytest.mark.parametrize("method, path", PROTECTED_ROUTES, ids=[
        f"{m} {p}" for m, p in PROTECTED_ROUTES
    ])
    def test_requires_auth(self, auth_client: TestClient, method: str, path: str):
        response = auth_client.request(method, path)
        assert response.status_code == 401, f"{method} {path} should require auth"

    @pytest.mark.parametrize("method, path", PUBLIC_ROUTES, ids=[
        f"{m} {p}" for m, p in PUBLIC_ROUTES
    ])
    def test_public_routes_accessible(self, auth_client: TestClient, method: str, path: str):
        response = auth_client.request(method, path)
        assert response.status_code != 401, f"{method} {path} should be public"
