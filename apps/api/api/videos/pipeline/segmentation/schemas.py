"""Segmentation schemas."""

from enum import Enum

from pydantic import BaseModel, Field

from api.core.schemas import AICost


class KenBurnsDirection(str, Enum):
    zoom_in = "zoom_in"
    zoom_out = "zoom_out"
    pan_left = "pan_left"
    pan_right = "pan_right"
    pan_up = "pan_up"
    pan_down = "pan_down"


class KenBurnsConfig(BaseModel):
    direction: KenBurnsDirection
    scale: float = Field(ge=1.1, le=1.4)


class SegmentResult(BaseModel):
    """LLM output — word index range, image prompt, and Ken Burns config.

    The LLM references words by index (from the numbered word list it receives).
    Timing is resolved by looking up word timestamps directly — no fuzzy matching.
    """

    order: int
    start_word_index: int
    end_word_index: int
    image_prompt: str
    ken_burns_config: KenBurnsConfig

    model_config = {"frozen": True}


class SegmentWithTiming(BaseModel):
    """Segment with resolved text and TTS timing. Used by all downstream stages."""

    order: int
    text: str
    image_prompt: str
    ken_burns_config: KenBurnsConfig
    start_time: float
    end_time: float

    model_config = {"frozen": True}


class SegmentationResult(BaseModel):
    """Full segmentation output with TTS-aligned timing."""

    segments: list[SegmentWithTiming]
    prompt: str
    cost: AICost = AICost()

    model_config = {"frozen": True}


class SegmentationOutput(BaseModel):
    """LLM structured output wrapper."""

    segments: list[SegmentResult]
