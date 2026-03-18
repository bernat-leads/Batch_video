"""Tests for video input validation rules.

Verifies that schema-level and route-level constraints reject invalid data
and accept valid data for video-related endpoints.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from api.videos.schemas import VideoCreate, VideoUpdate
from api.videos.pipeline.tts.schemas import TTSInput, WordTimestamp
from api.videos.pipeline.segmentation.schemas import SegmentationInput
from api.shots.schemas import ShotBase, ShotCreate, ShotUpdate


# ---------------------------------------------------------------------------
# VideoCreate validation
# ---------------------------------------------------------------------------


class TestVideoCreateValidation:
    """Business rules for creating a video."""

    def test_empty_script_text_is_rejected(self):
        with pytest.raises(ValidationError, match="script_text"):
            VideoCreate(script_text="", voice_id="v1")

    def test_missing_voice_id_is_rejected(self):
        with pytest.raises(ValidationError, match="voice_id"):
            VideoCreate(script_text="hello")

    def test_empty_voice_id_is_rejected(self):
        with pytest.raises(ValidationError, match="voice_id"):
            VideoCreate(script_text="hello", voice_id="")

    def test_valid_input_is_accepted(self):
        video = VideoCreate(script_text="Buy our product today!", voice_id="v1")
        assert video.script_text == "Buy our product today!"
        assert video.voice_id == "v1"

    def test_voice_id_over_255_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="voice_id"):
            VideoCreate(script_text="ok", voice_id="x" * 256)

    def test_style_over_255_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="style"):
            VideoCreate(script_text="ok", voice_id="v1", style="x" * 256)

    def test_top_text_over_500_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="top_text"):
            VideoCreate(script_text="ok", voice_id="v1", top_text="x" * 501)

    def test_prompt_over_5000_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="prompt"):
            VideoCreate(script_text="ok", voice_id="v1", prompt="x" * 5001)

    def test_none_optional_fields_are_accepted(self):
        video = VideoCreate(script_text="hello", voice_id="v1")
        assert video.style is None
        assert video.top_text is None
        assert video.prompt is None


# ---------------------------------------------------------------------------
# VideoUpdate validation
# ---------------------------------------------------------------------------


class TestVideoUpdateValidation:
    """Business rules for updating a video."""

    def test_empty_script_text_update_is_rejected(self):
        with pytest.raises(ValidationError, match="script_text"):
            VideoUpdate(script_text="")

    def test_none_script_text_is_accepted(self):
        """None means 'do not update this field'."""
        update = VideoUpdate(script_text=None)
        assert update.script_text is None

    def test_voice_id_over_255_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="voice_id"):
            VideoUpdate(voice_id="x" * 256)

    def test_style_over_255_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="style"):
            VideoUpdate(style="x" * 256)

    def test_top_text_over_500_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="top_text"):
            VideoUpdate(top_text="x" * 501)


# ---------------------------------------------------------------------------
# Shot validation
# ---------------------------------------------------------------------------


class TestShotValidation:
    """Business rules for shot create/update."""

    def test_negative_order_is_rejected(self):
        with pytest.raises(ValidationError, match="order"):
            ShotCreate(
                video_id=uuid.uuid4(),
                order=-1,
                text="hello",
                image_prompt="a cat",
                start_time=0.0,
                end_time=1.0,
            )

    def test_zero_order_is_accepted(self):
        shot = ShotCreate(
            video_id=uuid.uuid4(),
            order=0,
            text="hello",
            image_prompt="a cat",
            start_time=0.0,
            end_time=1.0,
        )
        assert shot.order == 0

    def test_empty_text_is_rejected(self):
        with pytest.raises(ValidationError, match="text"):
            ShotCreate(
                video_id=uuid.uuid4(),
                order=0,
                text="",
                image_prompt="a cat",
                start_time=0.0,
                end_time=1.0,
            )

    def test_empty_image_prompt_is_rejected(self):
        with pytest.raises(ValidationError, match="image_prompt"):
            ShotCreate(
                video_id=uuid.uuid4(),
                order=0,
                text="hello",
                image_prompt="",
                start_time=0.0,
                end_time=1.0,
            )

    def test_negative_start_time_is_rejected(self):
        with pytest.raises(ValidationError, match="start_time"):
            ShotCreate(
                video_id=uuid.uuid4(),
                order=0,
                text="hello",
                image_prompt="a cat",
                start_time=-0.5,
                end_time=1.0,
            )

    def test_negative_end_time_is_rejected(self):
        with pytest.raises(ValidationError, match="end_time"):
            ShotCreate(
                video_id=uuid.uuid4(),
                order=0,
                text="hello",
                image_prompt="a cat",
                start_time=0.0,
                end_time=-1.0,
            )

    def test_update_negative_order_is_rejected(self):
        with pytest.raises(ValidationError, match="order"):
            ShotUpdate(order=-1)

    def test_update_empty_text_is_rejected(self):
        with pytest.raises(ValidationError, match="text"):
            ShotUpdate(text="")

    def test_update_negative_start_time_is_rejected(self):
        with pytest.raises(ValidationError, match="start_time"):
            ShotUpdate(start_time=-0.1)

    def test_update_none_fields_are_accepted(self):
        """None means 'do not update this field'."""
        update = ShotUpdate()
        assert update.order is None
        assert update.text is None
        assert update.start_time is None


# ---------------------------------------------------------------------------
# TTSInput validation
# ---------------------------------------------------------------------------


class TestTTSInputValidation:
    """Business rules for TTS input."""

    def test_empty_script_text_is_rejected(self):
        with pytest.raises(ValidationError, match="script_text"):
            TTSInput(script_text="", voice_id="v1")

    def test_missing_voice_id_is_rejected(self):
        with pytest.raises(ValidationError, match="voice_id"):
            TTSInput(script_text="Hello world")

    def test_valid_input_is_accepted(self):
        tts = TTSInput(script_text="Hello world", voice_id="v1")
        assert tts.script_text == "Hello world"
        assert tts.voice_id == "v1"


# ---------------------------------------------------------------------------
# SegmentationInput validation
# ---------------------------------------------------------------------------


class TestSegmentationInputValidation:
    """Business rules for segmentation input."""

    def test_empty_script_text_is_rejected(self):
        with pytest.raises(ValidationError, match="script_text"):
            SegmentationInput(script_text="", word_timestamps=[])

    def test_valid_script_text_is_accepted(self):
        seg = SegmentationInput(script_text="Hello world", word_timestamps=[])
        assert seg.script_text == "Hello world"


# ---------------------------------------------------------------------------
# WordTimestamp validation
# ---------------------------------------------------------------------------


class TestWordTimestampValidation:
    """Business rules for word timestamps."""

    def test_empty_word_is_rejected(self):
        with pytest.raises(ValidationError, match="word"):
            WordTimestamp(word="", start=0.0, end=0.5)

    def test_negative_start_is_rejected(self):
        with pytest.raises(ValidationError, match="start"):
            WordTimestamp(word="hello", start=-1.0, end=0.5)

    def test_negative_end_is_rejected(self):
        with pytest.raises(ValidationError, match="end"):
            WordTimestamp(word="hello", start=0.0, end=-0.5)


# ---------------------------------------------------------------------------
# Route-level pagination validation (via test client)
# ---------------------------------------------------------------------------


class TestVideoPaginationValidation:
    """Pagination query parameters enforce bounds at the route level."""

    @pytest.fixture(scope="class")
    def authed_client(self):
        from api.app import create_application
        from api.deps.auth import get_current_session
        from fastapi.testclient import TestClient

        app = create_application()
        app.dependency_overrides[get_current_session] = lambda: {"authenticated": True}
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_page_zero_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/videos/?page=0")
        assert resp.status_code == 422

    def test_page_negative_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/videos/?page=-1")
        assert resp.status_code == 422

    def test_page_size_zero_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/videos/?page_size=0")
        assert resp.status_code == 422

    def test_page_size_over_100_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/videos/?page_size=101")
        assert resp.status_code == 422

    def test_page_size_at_100_is_accepted(self, authed_client):
        with patch(
            "api.videos.crud.VideoCrud.get_multi",
            new_callable=AsyncMock,
        ) as mock_get:
            from api.core.schemas import PageResponse

            mock_get.return_value = PageResponse.create(
                items=[], total=0, page=1, page_size=100
            )
            resp = authed_client.get("/api/v1/videos/?page_size=100")
        assert resp.status_code == 200

    def test_create_video_empty_script_returns_422(self, authed_client):
        resp = authed_client.post(
            "/api/v1/videos/", json={"script_text": ""}
        )
        assert resp.status_code == 422
