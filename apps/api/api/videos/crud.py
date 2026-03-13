"""Video and Shot CRUD dependencies."""

from typing import Annotated

from fastapi import Depends

from api.core.crud import BaseCrud
from api.deps.db import SessionDep
from api.videos.models.shot import Shot
from api.videos.models.video import Video
from api.videos.schemas import ShotCreate, ShotUpdate, VideoCreate, VideoUpdate


class VideoCrud(BaseCrud[Video, VideoCreate, VideoUpdate]):
    """CRUD operations for videos."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Video)


class ShotCrud(BaseCrud[Shot, ShotCreate, ShotUpdate]):
    """CRUD operations for shots."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Shot)


VideoCrudDep = Annotated[VideoCrud, Depends()]
ShotCrudDep = Annotated[ShotCrud, Depends()]
