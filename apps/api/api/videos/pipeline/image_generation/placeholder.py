"""Placeholder image generation for development."""

import io

from PIL import Image

from api.videos.pipeline.image_generation.base import ImageGenService
from api.videos.pipeline.image_generation.schemas import ImageConfig, ImageGenResult


class PlaceholderImageGenService(ImageGenService):
    """Generates solid-color placeholder images for development."""

    def generate_image(self, image_prompt: str, config: ImageConfig) -> ImageGenResult:
        """Generate a placeholder image matching the config dimensions."""
        width, height = config.dimensions
        image = Image.new("RGB", (width, height), color=(30, 30, 30))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        return ImageGenResult(
            image_bytes=buffer.getvalue(),
            content_type=config.output_format,
        )
