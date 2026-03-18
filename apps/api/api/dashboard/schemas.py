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

    model_costs: dict[str, AICost] = {}
    total_cost_usd: float = 0.0

    avg_model_costs: dict[str, AICost] = {}
    avg_cost_usd: float = 0.0
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
