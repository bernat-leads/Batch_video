"""Pydantic schemas for Video API endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from api.shots.schemas import ShotRead
from api.videos.enums import VideoStage, VideoStatus


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
