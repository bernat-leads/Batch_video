"""Gemini Imagen image generation service."""

import logging

from google import genai
from google.genai import types as genai_types

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.videos.pipeline.config import IMAGEN_COST_PER_IMAGE, IMAGEN_MODEL
from api.videos.pipeline.image_generation.base import ImageGenService
from api.videos.pipeline.image_generation.schemas import ImageConfig, ImageGenResult
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class GeminiImageGenService(ImageGenService):
    """Gemini Imagen — generates images based on template config."""

    def __init__(self) -> None:
        """Initialize with Gemini API client."""
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @pipeline_retry()
    def generate_image(self, image_prompt: str, config: ImageConfig) -> ImageGenResult:
        """Generate an image using the prompt and template's image config."""
        logger.info("Imagen: generating image")

        try:
            response = self._client.models.generate_images(
                model=IMAGEN_MODEL,
                prompt=image_prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=config.aspect_ratio,
                    output_mime_type=config.output_format,
                ),
            )
        except Exception as error:
            raise PipelineStageError(
                "image_generation", f"Imagen API call failed: {error}"
            ) from error

        if not response.generated_images:
            raise PipelineStageError(
                "image_generation",
                f"Imagen returned no image (prompt likely blocked: {image_prompt[:200]})",
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
            cost=AICost(cost_usd=IMAGEN_COST_PER_IMAGE),
        )
