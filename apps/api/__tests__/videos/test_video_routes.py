"""Tests for video route edge cases using the full app."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.app import create_application
from api.settings import settings


@pytest.fixture
def authed_client():
    app = create_application()
    client = TestClient(app)
    # Login
    client.post("/api/v1/auth/login", json={"password": settings.APP_PASSWORD})
    return client


class TestDeleteVideoNotFound:
    def test_returns_404(self, authed_client):
        with patch(
            "api.videos.crud.VideoCrud.get",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = authed_client.delete(f"/api/v1/videos/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestDownloadVideoNotReady:
    def test_returns_404_for_nonexistent(self, authed_client):
        with patch(
            "api.videos.crud.VideoCrud.get", new_callable=AsyncMock, return_value=None
        ):
            resp = authed_client.get(f"/api/v1/videos/{uuid.uuid4()}/download")
        assert resp.status_code == 404

    def test_returns_400_when_still_processing(self, authed_client):
        mock_video = MagicMock()
        mock_video.status = "processing"
        mock_video.output_url = None
        with patch(
            "api.videos.crud.VideoCrud.get",
            new_callable=AsyncMock,
            return_value=mock_video,
        ):
            resp = authed_client.get(f"/api/v1/videos/{uuid.uuid4()}/download")
        assert resp.status_code == 400


class TestExportZipValidation:
    def test_no_video_ids_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/videos/export-zip")
        assert resp.status_code == 422

    def test_invalid_uuid_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/videos/export-zip?video_id=not-a-uuid")
        assert resp.status_code == 422
