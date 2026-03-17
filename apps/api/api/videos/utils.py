"""Shared utilities for video pipeline."""

import tempfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from api.settings import settings


@contextmanager
def temp_file(suffix: str):
    """Yield a temp file path that's cleaned up on exit."""
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            path = tmp.name
        yield path
    finally:
        if path:
            Path(path).unlink(missing_ok=True)


def composite_overlay(frame: np.ndarray, overlay: np.ndarray) -> np.ndarray:
    """Alpha-composite an RGBA overlay onto an RGB frame."""
    alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0
    rgb = overlay[:, :, :3].astype(np.float32)
    blended = frame.astype(np.float32) * (1 - alpha) + rgb * alpha
    return blended.astype(np.uint8)


def pipeline_retry():
    """Retry decorator: exponential backoff for transient API errors and rate limits."""
    from google.genai.errors import ClientError

    return retry(
        stop=stop_after_attempt(settings.PIPELINE_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=settings.PIPELINE_RETRY_WAIT_SECONDS, min=2, max=60
        ),
        retry=retry_if_exception_type(
            (ConnectionError, TimeoutError, OSError, ClientError)
        ),
        reraise=True,
    )
