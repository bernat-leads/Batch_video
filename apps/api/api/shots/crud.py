"""Shot CRUD operations."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from api.core.crud import BaseCrud
from api.deps.db import SessionDep
from api.shots.models.shot import Shot
from api.shots.schemas import ShotCreate, ShotUpdate


class ShotCrud(BaseCrud[Shot, ShotCreate, ShotUpdate]):
    """CRUD operations for shots."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Shot)

    async def get_by_video(self, video_id: uuid.UUID) -> list[Shot]:
        """Get all shots for a video, ordered by sequence."""
        stmt = select(self.model).where(Shot.video_id == video_id).order_by(Shot.order)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())


ShotCrudDep = Annotated[ShotCrud, Depends()]
