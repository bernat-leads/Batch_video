"""Gemini Imagen image generation service."""

import logging
import re
import time

from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.videos.pipeline.config import IMAGEN_MODEL
from api.videos.pipeline.costs import get_image_cost
from api.videos.pipeline.image_generation.base import ImageGenService
from api.videos.pipeline.image_generation.schemas import ImageConfig, ImageGenResult
from api.videos.pipeline.rate_limiter import gemini_limiter, wait_for_slot
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)

# Matches "Please retry in 57.943882059s" or "retryDelay': '57s'"
_RETRY_DELAY_PATTERN = re.compile(r"retry\s*(?:in|Delay['\"]:\s*['\"])\s*([\d.]+)s")
_DEFAULT_429_WAIT_SECONDS = 60


def _parse_retry_delay(error_message: str) -> float:
    """Extract the retry delay from a Gemini 429 error message."""
    match = _RETRY_DELAY_PATTERN.search(error_message)
    if match:
        return float(match.group(1))
    return _DEFAULT_429_WAIT_SECONDS


class GeminiImageGenService(ImageGenService):
    """Gemini Imagen — generates images based on template config."""

    def __init__(self) -> None:
        """Initialize with Gemini API client."""
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_image(self, image_prompt: str, config: ImageConfig) -> ImageGenResult:
        """Generate an image using the prompt and template's image config."""
        wait_for_slot(gemini_limiter, "gemini:imagen")
        return self._call_api(image_prompt, config)

    @pipeline_retry()
    def _call_api(self, image_prompt: str, config: ImageConfig) -> ImageGenResult:
        """Call the Gemini API. Handles 429 rate limits by sleeping and re-raising for retry."""
        logger.info("Imagen: generating image")

        try:
            response = self._client.models.generate_images(
                model=IMAGEN_MODEL,
                prompt=image_prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=config.aspect_ratio,
                    output_mime_type=config.output_format,
                    include_safety_attributes=True,
                ),
            )
        except ClientError as error:
            error_str = str(error)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                delay = _parse_retry_delay(error_str)
                logger.warning(
                    "Imagen: rate limited, sleeping %.1fs before retry", delay
                )
                time.sleep(delay)
                raise  # Re-raise ClientError — pipeline_retry will retry
            raise PipelineStageError(
                "image_generation", f"Imagen API call failed: {error}"
            ) from error
        except Exception as error:
            raise PipelineStageError(
                "image_generation", f"Imagen API call failed: {error}"
            ) from error

        if not response.generated_images:
            safety = response.positive_prompt_safety_attributes
            details = ""
            if safety and safety.categories:
                all_scores = [
                    f"{cat}={score:.2f}"
                    for cat, score in zip(
                        safety.categories, safety.scores or [], strict=False
                    )
                ]
                details = f" [{', '.join(all_scores)}]"
            raise PipelineStageError(
                "image_generation",
                f"Imagen blocked image generation{details} — prompt: {image_prompt[:200]}",
            )

        generated = response.generated_images[0]
        if generated.rai_filtered_reason:
            raise PipelineStageError(
                "image_generation",
                f"Imagen filtered: {generated.rai_filtered_reason} (prompt: {image_prompt[:200]})",
            )

        image_bytes = generated.image.image_bytes
        logger.info("Imagen: complete (%d bytes)", len(image_bytes))

        return ImageGenResult(
            image_bytes=image_bytes,
            content_type=config.output_format,
            cost=AICost(cost_usd=get_image_cost(IMAGEN_MODEL)),
        )
