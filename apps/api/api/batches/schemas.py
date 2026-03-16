"""Pydantic schemas for Batch API endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from api.batches.enums import BatchStatus
from api.core.schemas import AICost
from api.events.schemas import BaseEvent, EventType


class BatchCreate(BaseModel):
    """Schema for creating a batch."""

    name: str
    column_mapping: dict[str, str]
    file_name: str
    file_key: str = ""


class BatchUpdate(BaseModel):
    """Schema for updating a batch (all fields optional)."""

    name: str | None = None


class BatchRead(BaseModel):
    """Schema for reading a batch."""

    id: uuid.UUID
    name: str
    status: BatchStatus
    total_videos: int
    duration_ms: int = 0
    completed_count: int = 0
    failed_count: int = 0
    pending_count: int = 0
    column_mapping: dict | None = None
    file_name: str | None = None
    error_message: str | None = None

    tts: AICost = AICost()
    segmentation: AICost = AICost()
    image_generation: AICost = AICost()
    total: AICost = AICost()

    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# SSE event schemas
# ---------------------------------------------------------------------------


class BatchProcessResult(BaseModel):
    """Result of the process_batch Celery task."""

    batch_id: str
    videos_created: int = 0
    error: str | None = None

    model_config = {"frozen": True}


class BatchProgressEvent(BaseEvent):
    """Batch progress counter update event."""

    type: EventType = EventType.batch_progress
    batch_id: str
    status: str
