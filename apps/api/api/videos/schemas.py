"""Pydantic schemas for Video and Shot API endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shot schemas
# ---------------------------------------------------------------------------


class ShotBase(BaseModel):
    """Shared fields for shot schemas."""

    order: int
    text: str
    image_prompt: str
    ken_burns_config: dict[str, Any] | None = None
    start_time: float
    end_time: float


class ShotCreate(ShotBase):
    """Schema for creating a shot."""

    video_id: uuid.UUID


class ShotUpdate(BaseModel):
    """Schema for updating a shot (all fields optional)."""

    order: int | None = None
    text: str | None = None
    image_prompt: str | None = None
    ken_burns_config: dict[str, Any] | None = None
    start_time: float | None = None
    end_time: float | None = None
    image_url: str | None = None


class ShotRead(ShotBase):
    """Schema for reading a shot."""

    id: uuid.UUID
    video_id: uuid.UUID
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Video schemas
# ---------------------------------------------------------------------------


class VideoBase(BaseModel):
    """Shared fields for video schemas."""

    script_text: str
    voice_id: str | None = None
    style: str | None = None


class VideoCreate(VideoBase):
    """Schema for creating a video."""

    batch_id: uuid.UUID | None = None


class VideoUpdate(BaseModel):
    """Schema for updating a video (all fields optional)."""

    script_text: str | None = None
    voice_id: str | None = None
    style: str | None = None
    status: str | None = None
    current_stage: str | None = None
    error_message: str | None = None
    output_url: str | None = None


class VideoRead(VideoBase):
    """Schema for reading a video."""

    id: uuid.UUID
    batch_id: uuid.UUID | None = None
    status: str
    current_stage: str
    error_message: str | None = None
    output_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class VideoReadWithShots(VideoRead):
    """Schema for reading a video with its shots."""

    shots: list[ShotRead] = []
