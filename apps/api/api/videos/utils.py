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


def precompute_overlay(rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pre-compute alpha, inv_alpha, and premultiplied RGB from an RGBA overlay.

    Returns (alpha, inv_alpha, premultiplied_rgb) as float32 arrays.
    Call once per overlay, then use fast_composite per frame.
    """
    alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
    inv_alpha = 1.0 - alpha
    premultiplied_rgb = rgba[:, :, :3].astype(np.float32) * alpha
    return alpha, inv_alpha, premultiplied_rgb


def fast_composite(
    frame: np.ndarray,
    inv_alpha: np.ndarray,
    premultiplied_rgb: np.ndarray,
) -> np.ndarray:
    """Alpha-composite a pre-computed overlay onto an RGB frame."""
    return (frame.astype(np.float32) * inv_alpha + premultiplied_rgb).astype(np.uint8)


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
