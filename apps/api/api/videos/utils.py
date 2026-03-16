"""Shared utilities for video pipeline."""

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from api.settings import settings


def pipeline_retry():
    """Retry decorator: 3 attempts with exponential backoff for transient API errors."""
    return retry(
        stop=stop_after_attempt(settings.PIPELINE_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=settings.PIPELINE_RETRY_WAIT_SECONDS, min=2, max=30
        ),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True,
    )
