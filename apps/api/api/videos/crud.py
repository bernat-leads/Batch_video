"""Video and Shot CRUD dependencies."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select

from api.core.crud import BaseCrud
from api.core.schemas import PageResponse
from api.deps.db import SessionDep
from api.videos.models.shot import Shot
from api.videos.models.video import Video
from api.videos.schemas import ShotCreate, ShotUpdate, VideoCreate, VideoUpdate


class VideoCrud(BaseCrud[Video, VideoCreate, VideoUpdate]):
    """CRUD operations for videos."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Video)

    async def get_by_batch_id(
        self, batch_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> PageResponse:
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

    async def get_batch_summaries(self) -> list[dict]:
        """Get aggregate stats grouped by batch_id."""
        stmt = (
            select(
                Video.batch_id,
                func.count().label("total"),
                func.count().filter(Video.status == "completed").label("completed"),
                func.count().filter(Video.status == "failed").label("failed"),
                func.count().filter(Video.status == "processing").label("processing"),
                func.count().filter(Video.status == "pending").label("pending"),
                func.min(Video.created_at).label("created_at"),
            )
            .where(Video.batch_id.isnot(None))
            .group_by(Video.batch_id)
            .order_by(func.min(Video.created_at).desc())
        )
        result = await self.db_session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]


class ShotCrud(BaseCrud[Shot, ShotCreate, ShotUpdate]):
    """CRUD operations for shots."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Shot)


VideoCrudDep = Annotated[VideoCrud, Depends()]
ShotCrudDep = Annotated[ShotCrud, Depends()]
