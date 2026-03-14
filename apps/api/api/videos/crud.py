"""Video CRUD operations."""

import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from api.batches.models.batch import Batch
from api.core.crud import BaseCrud
from api.core.schemas import PageResponse
from api.deps.db import SessionDep
from api.videos.enums import VideoStatus
from api.videos.models.video import Video
from api.videos.schemas import DailyStats, DashboardStats, VideoCreate, VideoUpdate


class VideoCrud(BaseCrud[Video, VideoCreate, VideoUpdate]):
    """CRUD operations for videos."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Video)

    async def get_with_shots(self, video_id: uuid.UUID) -> Video | None:
        """Get a video by ID with shots eagerly loaded."""
        stmt = (
            select(Video).options(selectinload(Video.shots)).where(Video.id == video_id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_by_batch_id(
        self, batch_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> "PageResponse[Video]":
        """Get videos filtered by batch_id."""
        count_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(Video.batch_id == batch_id)
        )
        total = (await self.db_session.execute(count_stmt)).scalar_one() or 0
        offset = (page - 1) * page_size
        stmt = (
            select(self.model)
            .where(Video.batch_id == batch_id)
            .order_by(Video.created_at)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(stmt)
        items = list(result.scalars().all())
        return PageResponse.create(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_dashboard_stats(self) -> DashboardStats:
        """Get aggregated dashboard statistics."""
        status_counts = await self.db_session.execute(
            select(
                func.count(Video.id).label("total"),
                func.count()
                .filter(Video.status == VideoStatus.completed)
                .label("completed"),
                func.count().filter(Video.status == VideoStatus.failed).label("failed"),
                func.count()
                .filter(Video.status == VideoStatus.processing)
                .label("processing"),
            )
        )
        counts = status_counts.one()

        aggs = await self.db_session.execute(
            select(
                func.coalesce(func.sum(Video.tokens_used), 0).label("total_tokens"),
                func.coalesce(func.sum(Video.generation_time_ms), 0).label(
                    "total_gen_time"
                ),
                func.coalesce(func.sum(Video.total_cost_usd), 0.0).label("total_cost"),
            )
        )
        agg = aggs.one()

        batch_count = await self.db_session.execute(select(func.count(Batch.id)))
        total_batches = batch_count.scalar_one()

        total = counts.total or 1
        return DashboardStats(
            total_videos=counts.total,
            completed_videos=counts.completed,
            failed_videos=counts.failed,
            processing_videos=counts.processing,
            total_batches=total_batches,
            total_tokens=agg.total_tokens,
            total_generation_time_ms=agg.total_gen_time,
            total_cost_usd=float(agg.total_cost),
            avg_tokens_per_video=round(agg.total_tokens / total, 1),
            avg_generation_time_ms=round(agg.total_gen_time / total, 1),
            avg_cost_per_video_usd=round(float(agg.total_cost) / total, 2),
        )

    async def get_daily_stats(self, days: int = 7) -> list[DailyStats]:
        """Get daily aggregated stats for the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db_session.execute(
            select(
                func.date(Video.created_at).label("date"),
                func.count(Video.id).label("videos"),
                func.coalesce(func.sum(Video.tokens_used), 0).label("tokens"),
                func.coalesce(func.sum(Video.generation_time_ms), 0).label(
                    "generation_time_ms"
                ),
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
                tokens=row.tokens,
                generation_time_ms=row.generation_time_ms,
                cost_usd=float(row.cost_usd),
            )
            for row in result.all()
        ]


VideoCrudDep = Annotated[VideoCrud, Depends()]
