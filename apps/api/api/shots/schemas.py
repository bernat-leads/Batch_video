"""Pydantic schemas for Shot API endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from api.shots.enums import ShotStatus
from api.videos.pipeline.segmentation.schemas import AnySegmentEffect


class ShotBase(BaseModel):
    """Shared fields for shot schemas."""

    order: int = Field(ge=0, description="Shot sequence order (zero-based)")
    text: str = Field(min_length=1, description="Script text for this shot")
    image_prompt: str = Field(min_length=1, description="Prompt for image generation")
    effect_config: AnySegmentEffect | None = None
    start_time: float = Field(ge=0, description="Start time in seconds")
    end_time: float = Field(ge=0, description="End time in seconds")


class ShotCreate(ShotBase):
    """Schema for creating a shot."""

    video_id: uuid.UUID


class ShotUpdate(BaseModel):
    """Schema for updating a shot (all fields optional)."""

    order: int | None = Field(default=None, ge=0)
    text: str | None = Field(default=None, min_length=1)
    image_prompt: str | None = Field(default=None, min_length=1)
    effect_config: AnySegmentEffect | None = None
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, ge=0)
    image_url: str | None = None


class ShotRead(ShotBase):
    """Schema for reading a shot."""

    id: uuid.UUID
    video_id: uuid.UUID
    image_url: str | None = None
    cost_usd: float = 0.0
    status: ShotStatus = ShotStatus.pending
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
