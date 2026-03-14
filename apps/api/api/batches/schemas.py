"""Pydantic schemas for Batch API endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


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
    completed_count: int = 0
    failed_count: int = 0
    processing_count: int = 0
    pending_count: int = 0
    column_mapping: dict | None = None
    file_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
