"""Pytest configuration and shared fixtures.

Provides reusable test fixtures for FastAPI test clients, mock database sessions,
and application instances used across the test suite.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.app import create_application
from api.core import router as core_router
from api.events.service import EventService
from api.storage import StorageService

# ---------------------------------------------------------------------------
# Core-only fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app_core_only() -> FastAPI:
    """Create a minimal FastAPI app with only core routes (no DB/lifespan)."""
    from api.deps.db import get_db
    from api.deps.redis import get_async_redis

    app = FastAPI(title="Test API")
    app.include_router(core_router)

    # Mock DB session that responds to execute(text("SELECT 1"))
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)

    async def _mock_get_db():
        yield mock_db

    # Mock Redis that responds to ping()
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    async def _mock_get_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = _mock_get_db
    app.dependency_overrides[get_async_redis] = _mock_get_redis
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
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_storage() -> MagicMock:
    """StorageService mock."""
    storage = MagicMock(spec=StorageService)
    storage.upload_file.return_value = None
    storage.download_file.return_value = b"mock file data"
    storage.delete_prefix.return_value = 3
    return storage


@pytest.fixture
def mock_events() -> AsyncMock:
    """EventService mock."""
    return AsyncMock(spec=EventService)
