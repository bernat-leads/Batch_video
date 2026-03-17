"""Abstract image generation service."""

from abc import ABC, abstractmethod

from api.videos.pipeline.image_generation.schemas import ImageConfig, ImageGenResult


class ImageGenService(ABC):
    """Abstract image generator — subclass for different providers."""

    @abstractmethod
    def generate_image(
        self, image_prompt: str, config: ImageConfig
    ) -> ImageGenResult:
        """Generate an image from a prompt using the given config."""
        ...
