"""Tests for file_name column — parsing, factory, schema, and download endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.batches.tasks import VIDEO_FIELDS
from api.parser import PandasFileParser, ParsedRow
from api.videos.models.video import Video
from api.videos.schemas import VideoCreate


def _parse(
    data: bytes,
    name: str = "f.csv",
    column_mapping: dict[str, str] | None = None,
) -> list[ParsedRow]:
    return PandasFileParser(data, name, column_mapping or {}, VIDEO_FIELDS).parse()


# ---------------------------------------------------------------------------
# Feature 1a: CSV parsing recognises the file_name column
# ---------------------------------------------------------------------------


class TestFileNameColumnParsing:
    """CSV rows with a file_name column parse the value into row data."""

    def test_file_name_column_parsed(self):
        csv = "script_text,voice_id,file_name\nHello,v1,my-video.mp4".encode()
        rows = _parse(csv)
        assert len(rows) == 1
        assert rows[0].is_valid is True
        assert rows[0].data["file_name"] == "my-video.mp4"

    def test_file_name_column_defaults_to_empty_string(self):
        csv = "script_text\nHello world".encode()
        rows = _parse(csv)
        assert rows[0].data["file_name"] == ""

    def test_file_name_column_whitespace_stripped(self):
        csv = "script_text,file_name\nHello,  my-video  ".encode()
        rows = _parse(csv)
        assert rows[0].data["file_name"] == "my-video"

    def test_file_name_column_with_mapping(self):
        csv = "script_text,output_name\nHello,custom-name.mp4".encode()
        rows = _parse(csv, column_mapping={"file_name": "output_name"})
        assert rows[0].data["file_name"] == "custom-name.mp4"


# ---------------------------------------------------------------------------
# Feature 1b: Video.from_parsed_row sets file_name
# ---------------------------------------------------------------------------


class TestVideoFromParsedRow:
    """Video.from_parsed_row() correctly maps file_name from parsed row data."""

    def test_sets_file_name_from_row(self):
        row = ParsedRow(
            data={
                "script_text": "Hello",
                "voice_id": "v1",
                "style": "cinematic",
                "top_text": "",
                "file_name": "my-ad.mp4",
            },
            is_valid=True,
            error_message=None,
        )
        batch_id = uuid.uuid4()
        video = Video.from_parsed_row(row, batch_id)

        assert video.file_name == "my-ad.mp4"
        assert video.batch_id == batch_id

    def test_file_name_none_when_empty_string(self):
        row = ParsedRow(
            data={
                "script_text": "Hello",
                "voice_id": "v1",
                "style": "",
                "top_text": "",
                "file_name": "",
            },
            is_valid=True,
            error_message=None,
        )
        video = Video.from_parsed_row(row, uuid.uuid4())
        assert video.file_name is None

    def test_file_name_none_when_missing(self):
        row = ParsedRow(
            data={"script_text": "Hello", "voice_id": "v1"},
            is_valid=True,
            error_message=None,
        )
        video = Video.from_parsed_row(row, uuid.uuid4())
        assert video.file_name is None


# ---------------------------------------------------------------------------
# Feature 1c: VideoCreate schema accepts file_name
# ---------------------------------------------------------------------------


class TestVideoCreateFileName:
    """VideoCreate schema validates the file_name field."""

    def test_accepts_file_name(self):
        schema = VideoCreate(
            script_text="Hello",
            voice_id="v1",
            file_name="my-output.mp4",
        )
        assert schema.file_name == "my-output.mp4"

    def test_file_name_defaults_to_none(self):
        schema = VideoCreate(script_text="Hello", voice_id="v1")
        assert schema.file_name is None

    def test_file_name_max_length_enforced(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VideoCreate(
                script_text="Hello",
                voice_id="v1",
                file_name="x" * 501,
            )


# ---------------------------------------------------------------------------
# Feature 1d: Download endpoint Content-Disposition uses file_name
# ---------------------------------------------------------------------------


def _mock_video(**kwargs) -> MagicMock:
    """Build a mock Video with sensible defaults for download tests."""
    defaults = dict(
        id=uuid.uuid4(),
        script_text="test",
        status="finished",
        current_stage="queued",
        batch_id=None,
        error_message=None,
        output_url="https://s3.example.com/video.mp4",
        output_s3_key="videos/output.mp4",
        voice_id=None,
        style=None,
        top_text=None,
        file_name=None,
        prompt="",
        duration_ms=0,
        model_costs={},
        total_cost_usd=0.0,
        file_size_bytes=0,
        created_at=None,
        updated_at=None,
        shots=[],
    )
    defaults.update(kwargs)
    video = MagicMock()
    for key, value in defaults.items():
        setattr(video, key, value)
    return video


class TestDownloadContentDisposition:
    """GET /videos/{id}/download sets Content-Disposition from file_name."""

    def test_uses_file_name_when_set(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        mock_video = _mock_video(id=video_id, file_name="my-ad")
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
        assert 'filename="my-ad.mp4"' in resp.headers["content-disposition"]

    def test_uses_file_name_with_mp4_extension(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        mock_video = _mock_video(id=video_id, file_name="my-ad.mp4")
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
        assert 'filename="my-ad.mp4"' in resp.headers["content-disposition"]

    def test_falls_back_to_id_when_no_file_name(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        mock_video = _mock_video(id=video_id, file_name=None)
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
        expected_name = f"video-{str(video_id)[:8]}.mp4"
        assert f'filename="{expected_name}"' in resp.headers["content-disposition"]
