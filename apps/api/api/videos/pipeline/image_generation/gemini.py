"""Gemini Imagen 3 image generation service."""

import logging

from google import genai
from google.genai import types as genai_types

from api.core.schemas import AICost
from api.settings import settings
from api.videos.pipeline.config import IMAGEN_COST_PER_IMAGE
from api.videos.pipeline.image_generation.base import ImageGenService
from api.videos.pipeline.image_generation.schemas import ImageGenResult
from api.videos.pipeline.segmentation.schemas import SegmentResult
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class GeminiImageGenService(ImageGenService):
    """Gemini Imagen 3 — generates 9:16 portrait images for video segments."""

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @pipeline_retry()
    def generate_image(self, segment: SegmentResult) -> ImageGenResult:
        """Generate a 9:16 portrait image from the segment's image prompt."""
        logger.info("Imagen 3: generating image for segment %d", segment.order)

        try:
            response = self._client.models.generate_images(
                model=settings.GEMINI_IMAGEN_MODEL,
                prompt=segment.image_prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",
                    output_mime_type="image/png",
                ),
            )
        except Exception as e:
            logger.error(
                "Imagen 3: API call failed for segment %d — %s", segment.order, e
            )
            raise

        image_bytes = response.generated_images[0].image.image_bytes

        logger.info(
            "Imagen 3: segment %d complete (%d bytes)",
            segment.order,
            len(image_bytes),
        )

        return ImageGenResult(
            image_bytes=image_bytes,
            content_type="image/png",
            cost=AICost(cost_usd=IMAGEN_COST_PER_IMAGE),
        )
