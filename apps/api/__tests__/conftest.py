"""Pytest configuration and shared fixtures.

Provides reusable test fixtures for FastAPI test clients, mock database sessions,
and application instances used across the test suite.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.app import create_application
from api.core import router as core_router


# ---------------------------------------------------------------------------
# Core-only fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app_core_only() -> FastAPI:
    """Create a minimal FastAPI app with only core routes (no DB/lifespan)."""
    app = FastAPI(title="Test API")
    app.include_router(core_router)
    return app


@pytest.fixture
def client(app_core_only: FastAPI) -> TestClient:
    """Provide a test client for the core-only app. No database required."""
    return TestClient(app_core_only)


# ---------------------------------------------------------------------------
# Full-app fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app() -> FastAPI:
    """Create a full application instance with all routers."""
    return create_application()


@pytest.fixture
def authed_client(app: FastAPI) -> TestClient:
    """Provide a test client with no auth restrictions."""
    client = TestClient(app)
    yield client


# ---------------------------------------------------------------------------
# Mock DB session
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session() -> AsyncMock:
    """Provide a mocked AsyncSession with standard DB operations stubbed."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    session.add = MagicMock()
    return session
