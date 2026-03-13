"""Pydantic schemas for Video, Shot, and Batch API endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from api.videos.enums import VideoStage, VideoStatus


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
    tokens_used: int = 0
    generation_time_ms: int = 0
    cost_usd: float = 0.0
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Video schemas
# ---------------------------------------------------------------------------


class VideoBase(BaseModel):
    """Shared fields for video schemas."""

    script_text: str
    prompt: str = ""
    voice_id: str | None = None
    style: str | None = None
    top_text: str | None = None


class VideoCreate(VideoBase):
    """Schema for creating a video."""

    batch_id: uuid.UUID | None = None


class VideoUpdate(BaseModel):
    """Schema for updating a video (all fields optional)."""

    script_text: str | None = None
    prompt: str | None = None
    voice_id: str | None = None
    style: str | None = None
    top_text: str | None = None
    status: VideoStatus | None = None
    current_stage: VideoStage | None = None
    error_message: str | None = None
    output_url: str | None = None


class VideoRead(VideoBase):
    """Schema for reading a video."""

    id: uuid.UUID
    batch_id: uuid.UUID | None = None
    status: VideoStatus
    current_stage: VideoStage
    error_message: str | None = None
    output_url: str | None = None
    tokens_used: int = 0
    generation_time_ms: int = 0
    total_cost_usd: float = 0.0
    avg_cost_per_shot_usd: float = 0.0
    file_size_bytes: int = 0
    width: int = 1080
    height: int = 1920
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class VideoReadWithShots(VideoRead):
    """Schema for reading a video with its shots."""

    shots: list[ShotRead] = []
    avg_tokens_per_shot: int = 0
    avg_generation_time_per_shot_ms: int = 0


# ---------------------------------------------------------------------------
# Dashboard stats schemas
# ---------------------------------------------------------------------------


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""

    total_videos: int
    completed_videos: int
    failed_videos: int
    processing_videos: int
    total_batches: int
    total_tokens: int
    total_generation_time_ms: int
    total_cost_usd: float
    avg_tokens_per_video: float
    avg_generation_time_ms: float
    avg_cost_per_video_usd: float


class DailyStats(BaseModel):
    """Stats for a single day."""

    date: str
    videos: int
    tokens: int
    generation_time_ms: int
    cost_usd: float


class DashboardResponse(BaseModel):
    """Full dashboard response."""

    stats: DashboardStats
    daily: list[DailyStats]


# ---------------------------------------------------------------------------
# Batch schemas
# ---------------------------------------------------------------------------


class BatchVideoItem(BaseModel):
    """Schema for a video item within a batch creation request."""

    script_text: str
    prompt: str = ""
    voice_id: str | None = None
    style: str | None = None
    top_text: str | None = None


class BatchCreate(BaseModel):
    """Schema for creating a batch with videos."""

    name: str
    videos: list[BatchVideoItem] = []


class BatchUpdate(BaseModel):
    """Schema for updating a batch (all fields optional)."""

    name: str | None = None
    tokens_used: int | None = None
    generation_time_ms: int | None = None
    total_cost_usd: float | None = None
    avg_cost_per_video_usd: float | None = None


class BatchRead(BaseModel):
    """Schema for reading a batch with computed video stats."""

    id: uuid.UUID
    name: str
    total_videos: int
    tokens_used: int = 0
    generation_time_ms: int = 0
    total_cost_usd: float = 0.0
    avg_cost_per_video_usd: float = 0.0
    completed: int = 0
    failed: int = 0
    processing: int = 0
    pending: int = 0
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
