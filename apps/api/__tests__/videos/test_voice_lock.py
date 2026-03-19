"""Tests for ElevenLabs voice_lock — distributed lock per voice_id."""

from unittest.mock import MagicMock, patch

import pytest
import redis.exceptions


class TestVoiceLockAcquireRelease:
    """voice_lock acquires and releases a Redis lock around the context."""

    def test_acquires_and_releases_lock(self):
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        mock_redis = MagicMock()
        mock_redis.lock.return_value = mock_lock

        with patch(
            "api.videos.pipeline.rate_limiter._lock_redis", mock_redis
        ):
            from api.videos.pipeline.rate_limiter import voice_lock

            with voice_lock("voice-123"):
                mock_lock.acquire.assert_called_once()

            mock_lock.release.assert_called_once()

    def test_lock_key_includes_voice_id(self):
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        mock_redis = MagicMock()
        mock_redis.lock.return_value = mock_lock

        with patch(
            "api.videos.pipeline.rate_limiter._lock_redis", mock_redis
        ):
            from api.videos.pipeline.rate_limiter import voice_lock

            with voice_lock("voice-abc"):
                pass

            mock_redis.lock.assert_called_once()
            call_args = mock_redis.lock.call_args
            assert call_args[0][0] == "tts:voice_lock:voice-abc"


class TestVoiceLockConcurrency:
    """Different voice_ids get independent locks."""

    def test_different_voice_ids_get_separate_locks(self):
        locks: dict[str, MagicMock] = {}

        def make_lock(key, **kwargs):
            lock = MagicMock()
            lock.acquire.return_value = True
            locks[key] = lock
            return lock

        mock_redis = MagicMock()
        mock_redis.lock.side_effect = make_lock

        with patch(
            "api.videos.pipeline.rate_limiter._lock_redis", mock_redis
        ):
            from api.videos.pipeline.rate_limiter import voice_lock

            with voice_lock("voice-1"):
                pass
            with voice_lock("voice-2"):
                pass

        assert "tts:voice_lock:voice-1" in locks
        assert "tts:voice_lock:voice-2" in locks
        assert locks["tts:voice_lock:voice-1"] is not locks["tts:voice_lock:voice-2"]


class TestVoiceLockTimeout:
    """Lock auto-releases on timeout — acquire returns False."""

    def test_logs_warning_when_lock_not_acquired(self):
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = False

        mock_redis = MagicMock()
        mock_redis.lock.return_value = mock_lock

        with patch(
            "api.videos.pipeline.rate_limiter._lock_redis", mock_redis
        ):
            from api.videos.pipeline.rate_limiter import voice_lock

            with voice_lock("voice-timeout"):
                pass

            # release should NOT be called when acquire returned False
            mock_lock.release.assert_not_called()


class TestVoiceLockNotOwnedError:
    """LockNotOwnedError on release is handled gracefully (lock expired)."""

    def test_handles_lock_not_owned_on_release(self):
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True
        mock_lock.release.side_effect = redis.exceptions.LockNotOwnedError(
            "lock expired"
        )

        mock_redis = MagicMock()
        mock_redis.lock.return_value = mock_lock

        with patch(
            "api.videos.pipeline.rate_limiter._lock_redis", mock_redis
        ):
            from api.videos.pipeline.rate_limiter import voice_lock

            # Should NOT raise — error is caught and logged
            with voice_lock("voice-expired"):
                pass

            mock_lock.release.assert_called_once()


class TestVoiceLockReleasesOnException:
    """Lock is released even if the body raises an exception."""

    def test_releases_lock_on_body_exception(self):
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        mock_redis = MagicMock()
        mock_redis.lock.return_value = mock_lock

        with patch(
            "api.videos.pipeline.rate_limiter._lock_redis", mock_redis
        ):
            from api.videos.pipeline.rate_limiter import voice_lock

            with pytest.raises(RuntimeError):
                with voice_lock("voice-err"):
                    raise RuntimeError("pipeline error")

            mock_lock.release.assert_called_once()
