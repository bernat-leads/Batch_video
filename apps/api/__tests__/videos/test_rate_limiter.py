"""Tests for per-provider rate limiting, concurrency control, and 429 handling."""

from unittest.mock import MagicMock, patch

import pytest

from api.videos.pipeline.image_generation.gemini import _parse_retry_delay
from api.videos.pipeline.rate_limiter import (
    _create_limiter,
    concurrency_slot,
    wait_for_slot,
)


class TestCreateLimiter:
    """_create_limiter returns a Throttled instance or None."""

    @pytest.mark.parametrize(
        "limit",
        [pytest.param(0, id="zero"), pytest.param(-1, id="negative")],
    )
    def test_returns_none_when_disabled(self, limit):
        assert _create_limiter("test", limit) is None

    def test_returns_throttled_when_positive(self):
        assert _create_limiter("test", 10) is not None


class TestWaitForSlot:
    """wait_for_slot blocks or skips based on limiter state."""

    def test_noop_when_limiter_is_none(self):
        wait_for_slot(None, "any-key")

    def test_calls_limit_on_active_limiter(self):
        mock_limiter = MagicMock()
        wait_for_slot(mock_limiter, "gemini:imagen")
        mock_limiter.limit.assert_called_once_with("gemini:imagen")


class TestConcurrencySlot:
    """concurrency_slot manages a Redis-backed distributed semaphore."""

    def test_noop_when_max_zero(self):
        """Disabled concurrency (limit=0) yields immediately."""
        with concurrency_slot("test", 0):
            pass

    def test_noop_when_max_negative(self):
        with concurrency_slot("test", -1):
            pass

    def test_acquires_and_releases_slot(self):
        """Slot is added to Redis on enter and removed on exit."""
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 0]  # 0 current slots
        mock_client.pipeline.return_value = mock_pipe
        mock_client.zadd.return_value = 1  # Successfully added

        with patch("api.videos.pipeline.rate_limiter.get_sync_redis", return_value=mock_client):
            with concurrency_slot("elevenlabs", 3):
                mock_client.zadd.assert_called_once()

            mock_client.zrem.assert_called_once()

    def test_waits_when_at_capacity(self):
        """When all slots are taken, polls until one frees up."""
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        # First call: at capacity (3/3), second call: slot freed (2/3)
        mock_pipe.execute.side_effect = [[None, 3], [None, 2]]
        mock_client.pipeline.return_value = mock_pipe
        mock_client.zadd.return_value = 1

        with (
            patch("api.videos.pipeline.rate_limiter.get_sync_redis", return_value=mock_client),
            patch("api.videos.pipeline.rate_limiter.time.sleep") as mock_sleep,
        ):
            with concurrency_slot("elevenlabs", 3):
                pass

        mock_sleep.assert_called_once()

    def test_releases_slot_on_exception(self):
        """Slot is released even if the wrapped code raises."""
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 0]
        mock_client.pipeline.return_value = mock_pipe
        mock_client.zadd.return_value = 1

        with patch("api.videos.pipeline.rate_limiter.get_sync_redis", return_value=mock_client):
            with pytest.raises(RuntimeError, match="API failed"):
                with concurrency_slot("elevenlabs", 3):
                    raise RuntimeError("API failed")

            mock_client.zrem.assert_called_once()


class TestParseRetryDelay:
    """Extract retry delay from Gemini 429 error messages."""

    @pytest.mark.parametrize(
        "message, expected",
        [
            pytest.param(
                "Please retry in 57.943882059s.",
                57.943882059,
                id="full-error-message",
            ),
            pytest.param(
                "retryDelay': '57s'",
                57.0,
                id="retry-info-format",
            ),
            pytest.param(
                "retry in 120.5s foo bar",
                120.5,
                id="embedded-in-text",
            ),
            pytest.param(
                "no delay info here",
                60.0,
                id="fallback-default",
            ),
            pytest.param(
                "",
                60.0,
                id="empty-string",
            ),
        ],
    )
    def test_parses_delay(self, message, expected):
        assert _parse_retry_delay(message) == expected


class TestGemini429Handling:
    """Gemini 429 errors sleep for the requested delay then re-raise for retry."""

    @pytest.fixture
    def gemini_service(self):
        from api.videos.pipeline.image_generation.gemini import GeminiImageGenService

        service = GeminiImageGenService.__new__(GeminiImageGenService)
        service._client = MagicMock()
        return service

    @pytest.fixture
    def image_config(self):
        from api.videos.pipeline.image_generation.schemas import ImageConfig

        return ImageConfig()

    def test_sleeps_on_429_and_reraises(self, gemini_service, image_config):
        from google.genai.errors import ClientError

        error_json = {
            "error": {
                "code": 429,
                "message": "Please retry in 30.5s.",
                "status": "RESOURCE_EXHAUSTED",
            }
        }
        gemini_service._client.models.generate_images.side_effect = ClientError(
            429, error_json
        )

        # Call __wrapped__ to bypass pipeline_retry — we're testing 429 handling, not retry
        with (
            patch("api.videos.pipeline.image_generation.gemini.time.sleep") as mock_sleep,
            pytest.raises(ClientError),
        ):
            gemini_service._call_api.__wrapped__(gemini_service, "test prompt", image_config)

        mock_sleep.assert_called_once_with(30.5)

    def test_non_429_client_error_becomes_pipeline_error(self, gemini_service, image_config):
        from google.genai.errors import ClientError

        from api.core.exceptions import PipelineStageError

        gemini_service._client.models.generate_images.side_effect = ClientError(
            400, {"error": {"code": 400, "message": "Bad request"}}
        )

        # Call __wrapped__ to bypass pipeline_retry
        with pytest.raises(PipelineStageError, match="image_generation"):
            gemini_service._call_api.__wrapped__(gemini_service, "test prompt", image_config)


class TestRetryIsolation:
    """Rate limiter runs outside pipeline_retry to avoid double-counting."""

    def test_gemini_wait_before_retry(self):
        call_order: list[str] = []

        with (
            patch(
                "api.videos.pipeline.image_generation.gemini.wait_for_slot",
                side_effect=lambda *_: call_order.append("wait"),
            ),
            patch(
                "api.videos.pipeline.image_generation.gemini.GeminiImageGenService._call_api",
                side_effect=lambda *_: call_order.append("api"),
            ),
        ):
            from api.videos.pipeline.image_generation.gemini import GeminiImageGenService

            service = GeminiImageGenService.__new__(GeminiImageGenService)
            service.generate_image("test prompt", MagicMock())

        assert call_order == ["wait", "api"]

    def test_elevenlabs_concurrency_wraps_retry(self):
        call_order: list[str] = []

        with (
            patch(
                "api.videos.pipeline.tts.elevenlabs.concurrency_slot",
                side_effect=lambda *_: (
                    call_order.append("semaphore"),
                    (yield),  # noqa: context manager
                ),
            ) as mock_slot,
            patch(
                "api.videos.pipeline.tts.elevenlabs.ElevenLabsTTSService._call_api",
                side_effect=lambda *_: call_order.append("api"),
            ),
        ):
            # concurrency_slot is a context manager — mock it properly
            from contextlib import contextmanager

            @contextmanager
            def fake_slot(provider, limit):
                call_order.append("semaphore_enter")
                yield
                call_order.append("semaphore_exit")

            mock_slot.side_effect = None
            with patch(
                "api.videos.pipeline.tts.elevenlabs.concurrency_slot",
                side_effect=fake_slot,
            ):
                from api.videos.pipeline.tts.elevenlabs import ElevenLabsTTSService

                service = ElevenLabsTTSService.__new__(ElevenLabsTTSService)
                service.synthesize(MagicMock())

        assert "semaphore_enter" in call_order
        assert "api" in call_order
