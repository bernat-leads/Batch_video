"""Tests for per-provider rate limiting."""

from unittest.mock import MagicMock, patch

import pytest

from api.videos.pipeline.rate_limiter import _create_limiter, wait_for_slot


class TestCreateLimiter:
    """_create_limiter returns a Throttled instance or None."""

    def test_returns_none_when_limit_is_zero(self):
        assert _create_limiter("test-provider", 0) is None

    def test_returns_none_when_limit_is_negative(self):
        assert _create_limiter("test-provider", -1) is None

    def test_returns_throttled_when_limit_is_positive(self):
        limiter = _create_limiter("test-provider", 10)
        assert limiter is not None


class TestWaitForSlot:
    """wait_for_slot blocks or skips based on limiter state."""

    def test_noop_when_limiter_is_none(self):
        """Disabled providers (limit=0) skip rate limiting entirely."""
        wait_for_slot(None, "any-key")  # Should not raise

    def test_calls_limit_on_active_limiter(self):
        mock_limiter = MagicMock()
        wait_for_slot(mock_limiter, "gemini:imagen")
        mock_limiter.limit.assert_called_once_with("gemini:imagen")

    def test_does_not_call_limit_when_none(self):
        """Ensure no attribute access on None."""
        wait_for_slot(None, "gemini:imagen")
        # If this doesn't raise AttributeError, it passes


class TestRateLimiterIntegration:
    """Integration tests using real Redis (skipped if Redis unavailable)."""

    @pytest.fixture
    def redis_limiter(self):
        """Create a real limiter with a tiny quota for testing."""
        limiter = _create_limiter("test-integration", 2)
        if limiter is None:
            pytest.skip("Limiter creation failed")
        return limiter

    def test_under_limit_proceeds_immediately(self, redis_limiter):
        """Requests under the limit should not block."""
        result = redis_limiter.limit("test:under-limit-1")
        assert result.limited is False

    def test_returns_result_object(self, redis_limiter):
        """limit() returns a RateLimitResult with limited flag."""
        result = redis_limiter.limit("test:result-check")
        assert hasattr(result, "limited")


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


class TestRetryIsolation:
    """Rate limiter runs outside pipeline_retry to avoid double-counting."""

    def test_gemini_generate_image_calls_wait_before_retry(self):
        """verify wait_for_slot is called before _call_api."""
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
            from api.videos.pipeline.image_generation.gemini import (
                GeminiImageGenService,
            )

            service = GeminiImageGenService.__new__(GeminiImageGenService)
            service.generate_image("test prompt", MagicMock())

        assert call_order == ["wait", "api"]
