"""Dashboard CRUD — read-only aggregate queries."""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select

from api.batches.models.batch import Batch
from api.core.schemas import AICost
from api.dashboard.schemas import DailyStats, DashboardStats
from api.deps.db import SessionDep
from api.videos.enums import VideoStatus
from api.videos.models.video import Video


class DashboardCrud:
    """Read-only aggregate queries for the dashboard."""

    def __init__(self, session: SessionDep) -> None:
        self._session = session

    async def get_stats(self) -> DashboardStats:
        status_counts = await self._session.execute(
            select(
                func.count(Video.id).label("total"),
                func.count()
                .filter(Video.status == VideoStatus.finished)
                .label("completed"),
                func.count().filter(Video.status == VideoStatus.failed).label("failed"),
                func.count()
                .filter(Video.status == VideoStatus.processing)
                .label("processing"),
            )
        )
        counts = status_counts.one()

        aggs = await self._session.execute(
            select(
                func.coalesce(func.sum(Video.duration_ms), 0).label("total_duration"),
                func.coalesce(func.sum(Video.total_cost_usd), 0.0).label("total_cost"),
            )
        )
        agg = aggs.one()

        batch_count = await self._session.execute(select(func.count(Batch.id)))
        total_batches = batch_count.scalar_one()

        video_count = counts.total or 1

        # Aggregate model_costs from all videos
        all_model_costs = (
            (await self._session.execute(select(Video.model_costs))).scalars().all()
        )

        merged: dict[str, dict[str, float | int]] = {}
        for mc in all_model_costs:
            for model, costs in (mc or {}).items():
                if model not in merged:
                    merged[model] = {"token_count": 0, "cost_usd": 0.0}
                merged[model]["token_count"] += costs.get("token_count", 0)
                merged[model]["cost_usd"] += costs.get("cost_usd", 0.0)

        model_costs = {k: AICost(**v) for k, v in merged.items()}
        avg_model_costs = {
            k: AICost(
                token_count=round(v.token_count / video_count),
                cost_usd=round(v.cost_usd / video_count, 6),
            )
            for k, v in model_costs.items()
        }

        total_cost = float(agg.total_cost)
        return DashboardStats(
            total_videos=counts.total,
            completed_videos=counts.completed,
            failed_videos=counts.failed,
            processing_videos=counts.processing,
            total_batches=total_batches,
            total_duration_ms=agg.total_duration,
            model_costs=model_costs,
            total_cost_usd=total_cost,
            avg_model_costs=avg_model_costs,
            avg_cost_usd=round(total_cost / video_count, 6),
            avg_duration_ms=round(agg.total_duration / video_count, 1),
        )

    async def get_daily_stats(self, days: int = 7) -> list[DailyStats]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self._session.execute(
            select(
                func.date(Video.created_at).label("date"),
                func.count(Video.id).label("videos"),
                func.coalesce(func.sum(Video.duration_ms), 0).label("duration_ms"),
                func.coalesce(func.sum(Video.total_cost_usd), 0.0).label("cost_usd"),
            )
            .where(Video.created_at >= cutoff)
            .group_by(func.date(Video.created_at))
            .order_by(func.date(Video.created_at))
        )
        return [
            DailyStats(
                date=str(row.date),
                videos=row.videos,
                duration_ms=row.duration_ms,
                cost_usd=float(row.cost_usd),
            )
            for row in result.all()
        ]


DashboardCrudDep = Annotated[DashboardCrud, Depends()]
