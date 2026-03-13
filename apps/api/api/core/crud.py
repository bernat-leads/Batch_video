"""Base repository with common CRUD operations."""

import uuid
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

from api.deps.db import SessionDep, save

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class PageResultItem(BaseModel):
    """Paginated result item."""

    data: list[dict[str, Any]]
    page: int = 0
    next_page: int = 0


class BaseCrud(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base CRUD operations."""

    def __init__(self, session: SessionDep, model: type[ModelType]):
        """Initialize base CRUD.

        Args:
            session: Database session
            model: SQLAlchemy model class
        """
        self.db_session = session
        self.model = model

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_data = (
            obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
        )
        # Exclude None so SQLAlchemy can use column defaults (e.g. id, created_at)
        obj_data = {k: v for k, v in obj_data.items() if v is not None}
        db_obj = self.model(**obj_data)
        await save(self.db_session, db_obj)
        return db_obj

    async def get(self, record_id: uuid.UUID) -> ModelType | None:
        """Get a record by ID."""
        return await self.db_session.get(self.model, record_id)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get multiple records with pagination."""
        statement = select(self.model).offset(skip).limit(limit)
        result = await self.db_session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self, record_id: uuid.UUID, obj_in: UpdateSchemaType
    ) -> ModelType | None:
        """Update a record."""
        db_obj = await self.get(record_id)
        if not db_obj:
            return None

        obj_data = (
            obj_in.model_dump(exclude_unset=True)
            if hasattr(obj_in, "model_dump")
            else obj_in.dict(exclude_unset=True)
        )
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await save(self.db_session, db_obj)
        return db_obj

    async def delete(self, record_id: uuid.UUID) -> bool:
        """Delete a record."""
        db_obj = await self.get(record_id)
        if not db_obj:
            return False

        await self.db_session.delete(db_obj)
        await self.db_session.commit()
        return True

    async def count(self) -> int:
        """Count total records."""
        from sqlalchemy import func

        # pylint: disable=E1102:not-callable
        statement = select(func.count()).select_from(self.model)
        result = await self.db_session.execute(statement)
        return result.scalar_one() or 0

    async def exists(self, record_id: uuid.UUID) -> bool:
        """Check if a record exists."""
        return await self.get(record_id) is not None
