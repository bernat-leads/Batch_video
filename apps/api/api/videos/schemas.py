"""Pydantic schemas for Video API endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from api.core.schemas import AICost
from api.events.schemas import BaseEvent, EventType
from api.shots.schemas import ShotRead
from api.videos.enums import VideoStage, VideoStatus


class VideoStatusCounts(BaseModel):
    """Video count breakdown by status for a batch."""

    finished: int = 0
    failed: int = 0
    processing: int = 0


class VideoCostTotals(BaseModel):
    """Aggregated cost and duration totals for a batch."""

    duration_ms: int = 0
    tts: AICost = AICost()
    segmentation: AICost = AICost()
    image_generation: AICost = AICost()
    total: AICost = AICost()


# ---------------------------------------------------------------------------
# Video schemas
# ---------------------------------------------------------------------------


class VideoCreate(BaseModel):
    """Schema for creating a video (also used as pipeline input)."""

    script_text: str
    voice_id: str | None = None
    style: str | None = None
    top_text: str | None = None
    prompt: str | None = None
    batch_id: uuid.UUID | None = None


class VideoUpdate(BaseModel):
    """Schema for updating a video (all fields optional)."""

    script_text: str | None = None
    voice_id: str | None = None
    style: str | None = None
    top_text: str | None = None
    status: VideoStatus | None = None
    current_stage: VideoStage | None = None
    error_message: str | None = None
    output_url: str | None = None


class VideoRead(BaseModel):
    """Schema for reading a video."""

    id: uuid.UUID
    batch_id: uuid.UUID | None = None
    script_text: str
    voice_id: str | None = None
    style: str | None = None
    top_text: str | None = None
    prompt: str | None = None
    status: VideoStatus
    current_stage: VideoStage
    error_message: str | None = None
    output_url: str | None = None
    duration_ms: int = 0
    file_size_bytes: int = 0
    width: int = 1080
    height: int = 1920

    tts: AICost = AICost()
    segmentation: AICost = AICost()
    image_generation: AICost = AICost()
    total: AICost = AICost()

    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class VideoReadWithShots(VideoRead):
    """Schema for reading a video with its shots."""

    shots: list[ShotRead] = []


# ---------------------------------------------------------------------------
# Pipeline result schemas
# ---------------------------------------------------------------------------


class VideoGenerationResult(BaseModel):
    """Returned by VideoService.generate_video after a successful pipeline run."""

    video_id: str
    video_r2_key: str
    file_size_bytes: int
    duration_ms: int
    num_shots: int
    tts: AICost
    segmentation: AICost
    image_generation: AICost
    total: AICost

    model_config = {"frozen": True}


# ---------------------------------------------------------------------------
# SSE event schemas
# ---------------------------------------------------------------------------


class VideoProgressEvent(BaseEvent):
    """Video pipeline stage transition event."""

    type: EventType = EventType.video_progress
    video_id: str
    batch_id: str | None = None
    status: str
    stage: str
