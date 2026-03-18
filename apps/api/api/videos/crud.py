"""Video CRUD operations."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from api.core.crud import BaseCrud
from api.core.schemas import AICost, PageResponse
from api.deps.db import SessionDep
from api.videos.enums import VideoStatus
from api.videos.models.video import Video
from api.videos.schemas import (
    VideoCostTotals,
    VideoCreate,
    VideoStatusCounts,
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
            .order_by(Video.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(stmt)
        items = list(result.scalars().all())
        return PageResponse.create(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_status_counts_by_batch(
        self, batch_id: uuid.UUID
    ) -> VideoStatusCounts:
        """Get video count breakdown by status for a batch."""
        row = (
            await self.db_session.execute(
                select(
                    func.count()
                    .filter(Video.status == VideoStatus.finished)
                    .label("finished"),
                    func.count()
                    .filter(Video.status == VideoStatus.failed)
                    .label("failed"),
                    func.count()
                    .filter(Video.status == VideoStatus.processing)
                    .label("processing"),
                ).where(Video.batch_id == batch_id)
            )
        ).one()
        return VideoStatusCounts(
            finished=row.finished, failed=row.failed, processing=row.processing
        )

    async def get_cost_totals_by_batch(self, batch_id: uuid.UUID) -> VideoCostTotals:
        """Get aggregated cost and duration totals for a batch."""
        row = (
            await self.db_session.execute(
                select(
                    func.coalesce(func.sum(Video.duration_ms), 0).label("duration"),
                    func.coalesce(func.sum(Video.total_cost_usd), 0.0).label(
                        "total_cost"
                    ),
                ).where(Video.batch_id == batch_id)
            )
        ).one()

        # Aggregate model_costs from individual videos
        video_costs = (
            await self.db_session.execute(
                select(Video.model_costs).where(Video.batch_id == batch_id)
            )
        ).scalars().all()

        merged: dict[str, dict[str, float | int]] = {}
        for mc in video_costs:
            for model, costs in (mc or {}).items():
                if model not in merged:
                    merged[model] = {"token_count": 0, "cost_usd": 0.0}
                merged[model]["token_count"] += costs.get("token_count", 0)
                merged[model]["cost_usd"] += costs.get("cost_usd", 0.0)

        return VideoCostTotals(
            duration_ms=row.duration,
            model_costs={k: AICost(**v) for k, v in merged.items()},
            total_cost_usd=float(row.total_cost),
        )

    async def get_finished_by_ids(self, video_ids: list[uuid.UUID]) -> list[Video]:
        """Get finished videos by a list of IDs."""
        stmt = select(Video).where(
            Video.id.in_(video_ids),
            Video.status == VideoStatus.finished,
            Video.output_url.is_not(None),
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def get_finished_by_batch(self, batch_id: uuid.UUID) -> list[Video]:
        """Get all finished videos for a batch."""
        stmt = (
            select(Video)
            .where(Video.batch_id == batch_id, Video.status == VideoStatus.finished)
            .order_by(Video.created_at)
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def create_bulk(self, videos: list[Video]) -> list[Video]:
        """Persist multiple video records."""
        for video in videos:
            self.db_session.add(video)
        await self.db_session.flush()
        await self.db_session.commit()
        return videos


VideoCrudDep = Annotated[VideoCrud, Depends()]
