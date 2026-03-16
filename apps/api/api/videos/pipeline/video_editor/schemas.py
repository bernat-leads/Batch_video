"""Video editor schemas."""

from pydantic import BaseModel

from api.videos.pipeline.segmentation.schemas import KenBurnsConfig


class Segment(BaseModel):
    """A single visual segment with image, timing, and camera movement."""

    image_bytes: bytes
    duration: float
    ken_burns: KenBurnsConfig


class CaptionWord(BaseModel):
    """A single word caption with timing."""

    word: str
    start: float
    end: float


class EditResult(BaseModel):
    """Output of the video editor."""

    video_bytes: bytes
    duration_ms: int

    model_config = {"frozen": True}
