"""Item CRUD operations — example BaseCrud subclass for the template."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from api.core.crud import BaseCrud
from api.deps.db import SessionDep
from api.items.models.item import Item
from api.items.schemas import ItemCreate, ItemUpdate


class ItemCrud(BaseCrud[Item, ItemCreate, ItemUpdate]):
    def __init__(self, session: SessionDep):
        super().__init__(session, Item)

    async def get_by_user_id(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        statement = (
            select(Item)
            .where(Item.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Item.created_at.desc())
        )
        result = await self.db_session.execute(statement)
        return list(result.scalars().all())


ItemCrudDep = Annotated[ItemCrud, Depends(ItemCrud)]
