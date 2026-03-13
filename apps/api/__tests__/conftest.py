"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.checkpointer import get_checkpointer
from api.app import create_application
from api.core import router as core_router
from api.deps.auth import User, get_user


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FAKE_USER = User(
    id="user-test-123",
    email="test@example.com",
    name="Test User",
)


# ---------------------------------------------------------------------------
# Core-only fixtures (existing)
# ---------------------------------------------------------------------------


@pytest.fixture
def app_core_only() -> FastAPI:
    """Minimal FastAPI app with only core routes (no DB/lifespan). Use for unit tests."""
    app = FastAPI(title="Test API")
    app.include_router(core_router)
    return app


@pytest.fixture
def client(app_core_only: FastAPI) -> TestClient:
    """Test client for the core-only app. No database required."""
    return TestClient(app_core_only)


# ---------------------------------------------------------------------------
# Full-app fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app() -> FastAPI:
    """Full application with all routers. Checkpointer is mocked to avoid real DB pool."""
    application = create_application()
    application.dependency_overrides[get_checkpointer] = lambda: AsyncMock()
    return application


@pytest.fixture
def fake_user() -> User:
    return FAKE_USER


@pytest.fixture
def authed_client(app: FastAPI) -> TestClient:
    """TestClient with auth dependency overridden to return fake user."""
    app.dependency_overrides[get_user] = lambda: FAKE_USER
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client(app: FastAPI) -> TestClient:
    """TestClient with NO auth override — requests hit real auth and fail."""
    client = TestClient(app)
    yield client


# ---------------------------------------------------------------------------
# Mock DB session
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mocked AsyncSession for CRUD unit tests."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    session.add = MagicMock()
    return session
