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
    order: int
    text: str
    image_prompt: str
    ken_burns_config: KenBurnsConfig
    start_time: float
    end_time: float

    model_config = {"frozen": True}


class SegmentationResult(BaseModel):
    segments: list[SegmentResult]
    prompt: str
    cost: AICost = AICost()

    model_config = {"frozen": True}


class SegmentationOutput(BaseModel):
    """LLM structured output wrapper."""

    segments: list[SegmentResult]
