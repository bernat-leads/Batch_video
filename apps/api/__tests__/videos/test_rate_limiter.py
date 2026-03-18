"""Tests for per-provider rate limiting and 429 handling."""

from unittest.mock import MagicMock, patch

import pytest

from api.videos.pipeline.image_generation.gemini import _parse_retry_delay
from api.videos.pipeline.rate_limiter import _create_limiter, wait_for_slot


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


class TestProviderSeparation:
    """Each provider gets its own rate limit namespace."""

    def test_different_keys_are_independent(self):
        limiter = _create_limiter("test-separation", 1000)
        if limiter is None:
            pytest.skip("Limiter creation failed")

        result_a = limiter.limit("provider-a:call")
        result_b = limiter.limit("provider-b:call")

        assert result_a.limited is False
        assert result_b.limited is False


class TestParseRetryDelay:
    """Extract retry delay from Gemini 429 error messages."""

    @pytest.mark.parametrize(
        "message, expected",
        [
            pytest.param("Please retry in 57.943882059s.", 57.943882059, id="full-error"),
            pytest.param("retryDelay': '57s'", 57.0, id="retry-info-format"),
            pytest.param("retry in 120.5s foo bar", 120.5, id="embedded-in-text"),
            pytest.param("no delay info here", 60.0, id="fallback-default"),
            pytest.param("", 60.0, id="empty-string"),
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
