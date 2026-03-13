"""Video, Shot, and Batch CRUD dependencies."""

import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from api.core.crud import BaseCrud
from api.core.schemas import PageResponse
from api.deps.db import SessionDep
from api.videos.enums import VideoStatus
from api.videos.models.batch import Batch
from api.videos.models.shot import Shot
from api.videos.models.video import Video
from api.videos.schemas import (
    BatchCreate,
    BatchUpdate,
    ShotCreate,
    ShotUpdate,
    VideoCreate,
    VideoUpdate,
)


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

    async def get_dashboard_stats(self) -> dict:
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

        total = counts.total or 1  # avoid div-by-zero
        return {
            "total_videos": counts.total,
            "completed_videos": counts.completed,
            "failed_videos": counts.failed,
            "processing_videos": counts.processing,
            "total_batches": total_batches,
            "total_tokens": agg.total_tokens,
            "total_generation_time_ms": agg.total_gen_time,
            "total_cost_usd": float(agg.total_cost),
            "avg_tokens_per_video": round(agg.total_tokens / total, 1),
            "avg_generation_time_ms": round(agg.total_gen_time / total, 1),
            "avg_cost_per_video_usd": round(float(agg.total_cost) / total, 2),
        }

    async def get_daily_stats(self, days: int = 7) -> list[dict]:
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
            {
                "date": str(row.date),
                "videos": row.videos,
                "tokens": row.tokens,
                "generation_time_ms": row.generation_time_ms,
                "cost_usd": float(row.cost_usd),
            }
            for row in result.all()
        ]


class ShotCrud(BaseCrud[Shot, ShotCreate, ShotUpdate]):
    """CRUD operations for shots."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Shot)


class BatchCrud(BaseCrud[Batch, BatchCreate, BatchUpdate]):
    """CRUD operations for batches."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Batch)

    async def create_with_videos(self, obj_in: BatchCreate) -> Batch:
        """Create a batch and all its videos in a single transaction."""
        batch = Batch(
            name=obj_in.name,
            total_videos=len(obj_in.videos),
        )
        self.db_session.add(batch)
        await self.db_session.flush()

        for video_data in obj_in.videos:
            video = Video(
                batch_id=batch.id,
                script_text=video_data.script_text,
                prompt=video_data.prompt,
                voice_id=video_data.voice_id,
                style=video_data.style,
                top_text=video_data.top_text,
            )
            self.db_session.add(video)

        await self.db_session.commit()
        await self.db_session.refresh(batch)
        return batch

    async def get_with_stats(self, batch_id: uuid.UUID) -> dict | None:
        """Get a single batch with computed video status counts."""
        stmt = (
            select(
                Batch,
                func.count(Video.id).label("video_count"),
                func.count()
                .filter(Video.status == VideoStatus.completed)
                .label("completed"),
                func.count().filter(Video.status == VideoStatus.failed).label("failed"),
                func.count()
                .filter(Video.status == VideoStatus.processing)
                .label("processing"),
                func.count()
                .filter(Video.status == VideoStatus.pending)
                .label("pending"),
                func.coalesce(func.sum(Video.tokens_used), 0).label("sum_tokens"),
                func.coalesce(func.sum(Video.generation_time_ms), 0).label(
                    "sum_gen_time"
                ),
                func.coalesce(func.sum(Video.total_cost_usd), 0.0).label("sum_cost"),
            )
            .outerjoin(Video, Video.batch_id == Batch.id)
            .where(Batch.id == batch_id)
            .group_by(Batch.id)
        )
        result = await self.db_session.execute(stmt)
        row = result.one_or_none()
        if not row:
            return None
        batch_dict = {c.key: getattr(row.Batch, c.key) for c in Batch.__table__.columns}
        batch_dict["completed"] = row.completed
        batch_dict["failed"] = row.failed
        batch_dict["processing"] = row.processing
        batch_dict["pending"] = row.pending
        batch_dict["tokens_used"] = row.sum_tokens
        batch_dict["generation_time_ms"] = row.sum_gen_time
        batch_dict["total_cost_usd"] = float(row.sum_cost)
        total = row.video_count or 1
        batch_dict["avg_cost_per_video_usd"] = round(float(row.sum_cost) / total, 4)
        return batch_dict

    async def get_all_with_stats(
        self, page: int = 1, page_size: int = 50
    ) -> PageResponse[dict]:
        """Get batches with computed video status counts (paginated)."""
        # Count total batches
        count_stmt = select(func.count()).select_from(Batch)
        total = (await self.db_session.execute(count_stmt)).scalar_one() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(
                Batch,
                func.count(Video.id).label("video_count"),
                func.count()
                .filter(Video.status == VideoStatus.completed)
                .label("completed"),
                func.count().filter(Video.status == VideoStatus.failed).label("failed"),
                func.count()
                .filter(Video.status == VideoStatus.processing)
                .label("processing"),
                func.count()
                .filter(Video.status == VideoStatus.pending)
                .label("pending"),
                func.coalesce(func.sum(Video.tokens_used), 0).label("sum_tokens"),
                func.coalesce(func.sum(Video.generation_time_ms), 0).label(
                    "sum_gen_time"
                ),
                func.coalesce(func.sum(Video.total_cost_usd), 0.0).label("sum_cost"),
            )
            .outerjoin(Video, Video.batch_id == Batch.id)
            .group_by(Batch.id)
            .order_by(Batch.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(stmt)
        rows = []
        for row in result.all():
            batch_dict = {
                c.key: getattr(row.Batch, c.key) for c in Batch.__table__.columns
            }
            batch_dict["completed"] = row.completed
            batch_dict["failed"] = row.failed
            batch_dict["processing"] = row.processing
            batch_dict["pending"] = row.pending
            batch_dict["tokens_used"] = row.sum_tokens
            batch_dict["generation_time_ms"] = row.sum_gen_time
            batch_dict["total_cost_usd"] = float(row.sum_cost)
            vc = row.video_count or 1
            batch_dict["avg_cost_per_video_usd"] = round(float(row.sum_cost) / vc, 4)
            rows.append(batch_dict)
        return PageResponse.create(
            items=rows, total=total, page=page, page_size=page_size
        )


VideoCrudDep = Annotated[VideoCrud, Depends()]
ShotCrudDep = Annotated[ShotCrud, Depends()]
BatchCrudDep = Annotated[BatchCrud, Depends()]
