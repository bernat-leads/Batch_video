"""Pydantic schemas for Shot API endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


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
    tokens_used: int = 0
    generation_time_ms: int = 0
    cost_usd: float = 0.0
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
