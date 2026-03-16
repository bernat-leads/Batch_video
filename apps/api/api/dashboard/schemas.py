"""Dashboard schemas."""

from pydantic import BaseModel

from api.core.schemas import AICost


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""

    total_videos: int
    completed_videos: int
    failed_videos: int
    processing_videos: int
    total_batches: int
    total_duration_ms: int

    tts: AICost = AICost()
    segmentation: AICost = AICost()
    image_generation: AICost = AICost()
    total: AICost = AICost()

    avg_tts: AICost = AICost()
    avg_segmentation: AICost = AICost()
    avg_image_generation: AICost = AICost()
    avg_total: AICost = AICost()
    avg_duration_ms: float


class DailyStats(BaseModel):
    """Stats for a single day."""

    date: str
    videos: int
    cost_usd: float
    duration_ms: int


class DashboardResponse(BaseModel):
    """Full dashboard response."""

    stats: DashboardStats
    daily: list[DailyStats]
