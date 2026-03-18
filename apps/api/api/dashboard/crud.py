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
                func.coalesce(func.sum(Video.tts_cost_usd), 0.0).label("tts_cost"),
                func.coalesce(func.sum(Video.tts_token_count), 0).label("tts_tokens"),
                func.coalesce(func.sum(Video.segmentation_cost_usd), 0.0).label(
                    "seg_cost"
                ),
                func.coalesce(func.sum(Video.segmentation_token_count), 0).label(
                    "seg_tokens"
                ),
                func.coalesce(func.sum(Video.image_generation_cost_usd), 0.0).label(
                    "img_cost"
                ),
                func.coalesce(func.sum(Video.image_generation_token_count), 0).label(
                    "img_tokens"
                ),
                func.coalesce(func.sum(Video.total_cost_usd), 0.0).label("total_cost"),
                func.coalesce(func.sum(Video.total_token_count), 0).label(
                    "total_tokens"
                ),
            )
        )
        agg = aggs.one()

        batch_count = await self._session.execute(select(func.count(Batch.id)))
        total_batches = batch_count.scalar_one()

        video_count = counts.total or 1

        def _avg(cost: float, tokens: int) -> AICost:
            return AICost(
                token_count=round(tokens / video_count),
                cost_usd=round(cost / video_count, 6),
            )

        return DashboardStats(
            total_videos=counts.total,
            completed_videos=counts.completed,
            failed_videos=counts.failed,
            processing_videos=counts.processing,
            total_batches=total_batches,
            total_duration_ms=agg.total_duration,
            tts=AICost(token_count=agg.tts_tokens, cost_usd=float(agg.tts_cost)),
            segmentation=AICost(
                token_count=agg.seg_tokens, cost_usd=float(agg.seg_cost)
            ),
            image_generation=AICost(
                token_count=agg.img_tokens, cost_usd=float(agg.img_cost)
            ),
            total=AICost(token_count=agg.total_tokens, cost_usd=float(agg.total_cost)),
            avg_tts=_avg(float(agg.tts_cost), agg.tts_tokens),
            avg_segmentation=_avg(float(agg.seg_cost), agg.seg_tokens),
            avg_image_generation=_avg(float(agg.img_cost), agg.img_tokens),
            avg_total=_avg(float(agg.total_cost), agg.total_tokens),
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
