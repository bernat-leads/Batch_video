"""Placeholder image generation for development."""

import io

from PIL import Image

from api.videos.pipeline.config import HEIGHT, WIDTH
from api.videos.pipeline.image_generation.base import ImageGenService
from api.videos.pipeline.image_generation.schemas import ImageGenResult
from api.videos.pipeline.segmentation.schemas import SegmentResult


class PlaceholderImageGenService(ImageGenService):
    """Generates solid-color placeholder images for development."""

    def generate_image(self, segment: SegmentResult) -> ImageGenResult:
        img = Image.new("RGB", (WIDTH, HEIGHT), color=(30, 30, 30))
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        return ImageGenResult(
            image_bytes=buf.getvalue(),
            content_type="image/png",
        )
