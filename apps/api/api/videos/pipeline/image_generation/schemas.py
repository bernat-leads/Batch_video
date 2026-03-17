"""Image generation schemas."""

from pydantic import BaseModel

from api.core.schemas import AICost


_SIZE_MAP = {
    "1K": 1024,
    "2K": 2048,
}

_ASPECT_RATIOS = {
    "9:16": (9, 16),
    "16:9": (16, 9),
    "1:1": (1, 1),
    "4:3": (4, 3),
    "3:4": (3, 4),
}


class ImageConfig(BaseModel):
    """Configuration for image generation, provided by the video template."""

    aspect_ratio: str = "9:16"
    output_format: str = "image/png"
    size: str = "1K"

    @property
    def dimensions(self) -> tuple[int, int]:
        """Return (width, height) derived from aspect_ratio and size."""
        max_dim = _SIZE_MAP.get(self.size, 1024)
        ratio_w, ratio_h = _ASPECT_RATIOS.get(self.aspect_ratio, (9, 16))
        if ratio_w >= ratio_h:
            width = max_dim
            height = int(max_dim * ratio_h / ratio_w)
        else:
            height = max_dim
            width = int(max_dim * ratio_w / ratio_h)
        return width, height


class ImageGenResult(BaseModel):
    """Output of the image generator."""

    image_bytes: bytes
    content_type: str
    cost: AICost = AICost()

    model_config = {"frozen": True}
