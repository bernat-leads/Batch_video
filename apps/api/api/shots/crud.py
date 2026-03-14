"""Shot CRUD operations."""

from typing import Annotated

from fastapi import Depends

from api.core.crud import BaseCrud
from api.deps.db import SessionDep
from api.shots.models.shot import Shot
from api.shots.schemas import ShotCreate, ShotUpdate


class ShotCrud(BaseCrud[Shot, ShotCreate, ShotUpdate]):
    """CRUD operations for shots."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Shot)


ShotCrudDep = Annotated[ShotCrud, Depends()]
