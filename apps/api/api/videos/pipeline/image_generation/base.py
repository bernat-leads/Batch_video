"""Abstract image generation service."""

from abc import ABC, abstractmethod

from api.videos.pipeline.image_generation.schemas import ImageGenResult
from api.videos.pipeline.segmentation.schemas import SegmentResult


class ImageGenService(ABC):
    """Abstract image generator — subclass for different providers."""

    @abstractmethod
    def generate_image(self, segment: SegmentResult) -> ImageGenResult:
        """Generate an image from a segment's image prompt."""
        ...
