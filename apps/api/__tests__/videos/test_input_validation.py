"""Tests for video input validation rules.

Uses parametrize to test all field constraints in compact loops.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from api.shots.schemas import ShotCreate, ShotUpdate
from api.videos.pipeline.segmentation.schemas import SegmentationInput
from api.videos.pipeline.tts.schemas import TTSInput, WordTimestamp
from api.videos.schemas import VideoCreate, VideoUpdate


# ---------------------------------------------------------------------------
# Schema rejection tests — parametrized
# ---------------------------------------------------------------------------

VALID_SHOT_KWARGS = dict(
    video_id=uuid.uuid4(), order=0, text="hello",
    image_prompt="a cat", start_time=0.0, end_time=1.0,
)


@pytest.mark.parametrize(
    "schema, kwargs, match",
    [
        # VideoCreate rejections
        pytest.param(VideoCreate, dict(script_text="", voice_id="v1"), "script_text", id="video-create-empty-script"),
        pytest.param(VideoCreate, dict(script_text="hello"), "voice_id", id="video-create-missing-voice"),
        pytest.param(VideoCreate, dict(script_text="hello", voice_id=""), "voice_id", id="video-create-empty-voice"),
        pytest.param(VideoCreate, dict(script_text="ok", voice_id="x" * 256), "voice_id", id="video-create-voice-too-long"),
        pytest.param(VideoCreate, dict(script_text="ok", voice_id="v1", style="x" * 256), "style", id="video-create-style-too-long"),
        pytest.param(VideoCreate, dict(script_text="ok", voice_id="v1", top_text="x" * 501), "top_text", id="video-create-top-text-too-long"),
        pytest.param(VideoCreate, dict(script_text="ok", voice_id="v1", prompt="x" * 5001), "prompt", id="video-create-prompt-too-long"),
        # VideoUpdate rejections
        pytest.param(VideoUpdate, dict(script_text=""), "script_text", id="video-update-empty-script"),
        pytest.param(VideoUpdate, dict(voice_id="x" * 256), "voice_id", id="video-update-voice-too-long"),
        pytest.param(VideoUpdate, dict(style="x" * 256), "style", id="video-update-style-too-long"),
        pytest.param(VideoUpdate, dict(top_text="x" * 501), "top_text", id="video-update-top-text-too-long"),
        # ShotCreate rejections
        pytest.param(ShotCreate, {**VALID_SHOT_KWARGS, "order": -1}, "order", id="shot-create-negative-order"),
        pytest.param(ShotCreate, {**VALID_SHOT_KWARGS, "text": ""}, "text", id="shot-create-empty-text"),
        pytest.param(ShotCreate, {**VALID_SHOT_KWARGS, "image_prompt": ""}, "image_prompt", id="shot-create-empty-prompt"),
        pytest.param(ShotCreate, {**VALID_SHOT_KWARGS, "start_time": -0.5}, "start_time", id="shot-create-negative-start"),
        pytest.param(ShotCreate, {**VALID_SHOT_KWARGS, "end_time": -1.0}, "end_time", id="shot-create-negative-end"),
        # ShotUpdate rejections
        pytest.param(ShotUpdate, dict(order=-1), "order", id="shot-update-negative-order"),
        pytest.param(ShotUpdate, dict(text=""), "text", id="shot-update-empty-text"),
        pytest.param(ShotUpdate, dict(start_time=-0.1), "start_time", id="shot-update-negative-start"),
        # TTSInput rejections
        pytest.param(TTSInput, dict(script_text="", voice_id="v1"), "script_text", id="tts-empty-script"),
        pytest.param(TTSInput, dict(script_text="Hello world"), "voice_id", id="tts-missing-voice"),
        # SegmentationInput rejections
        pytest.param(SegmentationInput, dict(script_text="", word_timestamps=[]), "script_text", id="seg-empty-script"),
        # WordTimestamp rejections
        pytest.param(WordTimestamp, dict(word="", start=0.0, end=0.5), "word", id="word-empty"),
        pytest.param(WordTimestamp, dict(word="hello", start=-1.0, end=0.5), "start", id="word-negative-start"),
        pytest.param(WordTimestamp, dict(word="hello", start=0.0, end=-0.5), "end", id="word-negative-end"),
    ],
)
def test_schema_rejects_invalid_input(schema, kwargs, match):
    with pytest.raises(ValidationError, match=match):
        schema(**kwargs)


# ---------------------------------------------------------------------------
# Schema acceptance tests — parametrized
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "schema, kwargs, assertions",
    [
        pytest.param(
            VideoCreate,
            dict(script_text="Buy our product today!", voice_id="v1"),
            {"script_text": "Buy our product today!", "voice_id": "v1", "style": None, "top_text": None, "prompt": None},
            id="video-create-valid",
        ),
        pytest.param(
            VideoUpdate,
            dict(script_text=None),
            {"script_text": None},
            id="video-update-none-fields",
        ),
        pytest.param(
            ShotCreate,
            VALID_SHOT_KWARGS,
            {"order": 0, "text": "hello"},
            id="shot-create-valid",
        ),
        pytest.param(
            ShotUpdate,
            {},
            {"order": None, "text": None, "start_time": None},
            id="shot-update-none-fields",
        ),
        pytest.param(
            TTSInput,
            dict(script_text="Hello world", voice_id="v1"),
            {"script_text": "Hello world", "voice_id": "v1"},
            id="tts-valid",
        ),
        pytest.param(
            SegmentationInput,
            dict(script_text="Hello world", word_timestamps=[]),
            {"script_text": "Hello world"},
            id="seg-valid",
        ),
    ],
)
def test_schema_accepts_valid_input(schema, kwargs, assertions):
    obj = schema(**kwargs)
    for field, expected in assertions.items():
        assert getattr(obj, field) == expected


# ---------------------------------------------------------------------------
# Route-level pagination validation (via test client)
# ---------------------------------------------------------------------------


class TestVideoPaginationValidation:
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

    @pytest.mark.parametrize(
        "params",
        [
            pytest.param("page=0", id="page-zero"),
            pytest.param("page=-1", id="page-negative"),
            pytest.param("page_size=0", id="page-size-zero"),
            pytest.param("page_size=101", id="page-size-over-100"),
        ],
    )
    def test_invalid_pagination_returns_422(self, authed_client, params):
        assert authed_client.get(f"/api/v1/videos/?{params}").status_code == 422

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
        resp = authed_client.post("/api/v1/videos/", json={"script_text": ""})
        assert resp.status_code == 422
