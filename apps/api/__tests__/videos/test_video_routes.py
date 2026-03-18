"""Tests for video route edge cases — delete, download, retry, list, preview."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.app import create_application
from api.deps.auth import get_current_session


@pytest.fixture
def authed_client():
    """Provide a test client with auth bypassed via dependency override."""
    app = create_application()
    app.dependency_overrides[get_current_session] = lambda: {"authenticated": True}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _mock_video(**kwargs) -> MagicMock:
    """Build a mock Video with sensible defaults for route tests."""
    defaults = dict(
        id=uuid.uuid4(),
        script_text="test",
        status="processing",
        current_stage="queued",
        batch_id=None,
        error_message=None,
        output_url=None,
        output_s3_key=None,
        tts_cost_usd=0.0,
        tts_token_count=0,
        segmentation_cost_usd=0.0,
        segmentation_token_count=0,
        image_generation_cost_usd=0.0,
        image_generation_token_count=0,
        total_cost_usd=0.0,
        total_token_count=0,
        file_size_bytes=0,
        voice_id=None,
        style=None,
        top_text=None,
        prompt="",
        duration_ms=0,
        created_at=None,
        updated_at=None,
        shots=[],
    )
    defaults.update(kwargs)
    video = MagicMock()
    for key, value in defaults.items():
        setattr(video, key, value)
    return video


class TestDeleteVideoNotFound:
    """DELETE /videos/{id} returns 404 for non-existent video."""

    def test_returns_404(self, authed_client: TestClient):
        with patch(
            "api.videos.crud.VideoCrud.get",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = authed_client.delete(f"/api/v1/videos/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestDownloadVideoNotReady:
    """GET /videos/{id}/download handles missing and unfinished videos."""

    def test_returns_404_for_nonexistent(self, authed_client: TestClient):
        with patch(
            "api.videos.crud.VideoCrud.get", new_callable=AsyncMock, return_value=None
        ):
            resp = authed_client.get(f"/api/v1/videos/{uuid.uuid4()}/download")
        assert resp.status_code == 404

    def test_returns_400_when_still_processing(self, authed_client: TestClient):
        mock_video = _mock_video(status="processing", output_url=None)
        with patch(
            "api.videos.crud.VideoCrud.get",
            new_callable=AsyncMock,
            return_value=mock_video,
        ):
            resp = authed_client.get(f"/api/v1/videos/{uuid.uuid4()}/download")
        assert resp.status_code == 400


class TestExportZipValidation:
    """GET /videos/export-zip validates query parameters."""

    @pytest.mark.parametrize(
        "query,expected_status",
        [
            pytest.param("", 422, id="no-video-ids"),
            pytest.param("?video_id=not-a-uuid", 422, id="invalid-uuid"),
        ],
    )
    def test_invalid_params_return_422(
        self, authed_client: TestClient, query: str, expected_status: int
    ):
        resp = authed_client.get(f"/api/v1/videos/export-zip{query}")
        assert resp.status_code == expected_status


class TestRetryVideoNotFailed:
    """POST /videos/{id}/retry returns 400 for non-failed videos."""

    @pytest.mark.parametrize(
        "status",
        [
            pytest.param("processing", id="processing-video"),
            pytest.param("finished", id="finished-video"),
        ],
    )
    def test_retry_non_failed_returns_400(
        self, authed_client: TestClient, status: str
    ):
        video_id = uuid.uuid4()
        mock_video = _mock_video(id=video_id, status=status)
        with patch(
            "api.videos.crud.VideoCrud.get",
            new_callable=AsyncMock,
            return_value=mock_video,
        ):
            resp = authed_client.post(f"/api/v1/videos/{video_id}/retry")
        assert resp.status_code == 400
        assert "failed" in resp.json()["message"].lower()


class TestDownloadFinishedVideo:
    """GET /videos/{id}/download returns streaming response for finished video."""

    def test_download_finished_video_returns_200(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        mock_video = _mock_video(
            id=video_id,
            status="finished",
            output_url="https://s3.example.com/video.mp4",
            output_s3_key="videos/output.mp4",
        )
        with (
            patch(
                "api.videos.crud.VideoCrud.get",
                new_callable=AsyncMock,
                return_value=mock_video,
            ),
            patch(
                "api.storage.service.StorageService.stream_file",
                return_value=iter([b"video-bytes"]),
            ),
        ):
            resp = authed_client.get(f"/api/v1/videos/{video_id}/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "video/mp4"
