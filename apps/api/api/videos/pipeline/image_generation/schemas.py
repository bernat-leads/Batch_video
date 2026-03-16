"""Image generation schemas."""

from pydantic import BaseModel

from api.core.schemas import AICost


class ImageGenResult(BaseModel):
    image_bytes: bytes
    content_type: str
    cost: AICost = AICost()

    model_config = {"frozen": True}
