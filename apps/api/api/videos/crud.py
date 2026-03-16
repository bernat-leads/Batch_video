"""Video CRUD operations."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from api.core.crud import BaseCrud
from api.core.schemas import PageResponse
from api.deps.db import SessionDep
from api.videos.enums import VideoStatus
from api.videos.models.video import Video
from api.core.schemas import AICost
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
                    func.coalesce(func.sum(Video.tts_cost_usd), 0.0).label("tts_cost"),
                    func.coalesce(func.sum(Video.tts_token_count), 0).label(
                        "tts_tokens"
                    ),
                    func.coalesce(func.sum(Video.segmentation_cost_usd), 0.0).label(
                        "seg_cost"
                    ),
                    func.coalesce(func.sum(Video.segmentation_token_count), 0).label(
                        "seg_tokens"
                    ),
                    func.coalesce(func.sum(Video.image_generation_cost_usd), 0.0).label(
                        "img_cost"
                    ),
                    func.coalesce(
                        func.sum(Video.image_generation_token_count), 0
                    ).label("img_tokens"),
                    func.coalesce(func.sum(Video.total_cost_usd), 0.0).label(
                        "total_cost"
                    ),
                    func.coalesce(func.sum(Video.total_token_count), 0).label(
                        "total_tokens"
                    ),
                ).where(Video.batch_id == batch_id)
            )
        ).one()
        return VideoCostTotals(
            duration_ms=row.duration,
            tts=AICost(cost_usd=float(row.tts_cost), token_count=row.tts_tokens),
            segmentation=AICost(
                cost_usd=float(row.seg_cost), token_count=row.seg_tokens
            ),
            image_generation=AICost(
                cost_usd=float(row.img_cost), token_count=row.img_tokens
            ),
            total=AICost(cost_usd=float(row.total_cost), token_count=row.total_tokens),
        )

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
