"""Per-provider rate limiters backed by Redis.

Uses throttled-py with sliding window algorithm. Each provider gets its own
limiter configured from settings. Limiters block (sleep) until a slot opens —
the pipeline never breaks on rate limits. Set limit to 0 to disable.
"""

import logging
from contextlib import contextmanager
from typing import Generator

import redis
from throttled import RateLimiterType, RedisStore, Throttled, per_min

from api.settings import settings

logger = logging.getLogger(__name__)

_store = RedisStore(server=settings.CELERY_BROKER_URL)
_lock_redis = redis.from_url(settings.CELERY_BROKER_URL)


def _create_limiter(provider: str, limit: int) -> Throttled | None:
    """Create a rate limiter for a provider. Returns None if limit is 0 (disabled)."""
    if limit <= 0:
        logger.info("Rate limiting disabled for %s", provider)
        return None
    return Throttled(
        using=RateLimiterType.SLIDING_WINDOW.value,
        quota=per_min(limit),
        store=_store,
        timeout=None,  # Block forever — pipeline waits, never errors
    )


def wait_for_slot(limiter: Throttled | None, key: str) -> None:
    """Block until a rate limit slot is available. No-op if limiter is None."""
    if limiter is None:
        return
    limiter.limit(key)


@contextmanager
def voice_lock(voice_id: str) -> Generator[None, None, None]:
    """Acquire a distributed lock for a voice_id. Blocks until available.

    Prevents concurrent ElevenLabs TTS requests for the same voice,
    which causes 409 'already_running' errors.
    """
    lock_key = f"tts:voice_lock:{voice_id}"
    lock = _lock_redis.lock(
        lock_key,
        timeout=settings.ELEVENLABS_VOICE_LOCK_TIMEOUT,
        blocking=True,
        blocking_timeout=settings.ELEVENLABS_VOICE_LOCK_TIMEOUT,
    )
    acquired = lock.acquire()
    if not acquired:
        logger.warning(
            "Failed to acquire voice lock for %s after %ds",
            voice_id,
            settings.ELEVENLABS_VOICE_LOCK_TIMEOUT,
        )
    try:
        yield
    finally:
        try:
            if acquired:
                lock.release()
        except redis.exceptions.LockNotOwnedError:
            logger.debug("Voice lock %s expired before release", voice_id)


gemini_limiter = _create_limiter("gemini", settings.GEMINI_RATE_LIMIT)
openai_limiter = _create_limiter("openai", settings.OPENAI_RATE_LIMIT)
elevenlabs_limiter = _create_limiter("elevenlabs", settings.ELEVENLABS_RATE_LIMIT)
