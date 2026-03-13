"""Base repository with common CRUD operations."""

import uuid
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import DeclarativeBase

from api.core.schemas import PageResponse
from api.deps.db import SessionDep, save

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCrud(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base CRUD operations."""

    def __init__(self, session: SessionDep, model: type[ModelType]):
        self.db_session = session
        self.model = model

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_data)
        await save(self.db_session, db_obj)
        return db_obj

    async def get(self, record_id: uuid.UUID) -> ModelType | None:
        """Get a record by ID."""
        return await self.db_session.get(self.model, record_id)

    async def get_multi(self, page: int = 1, page_size: int = 50) -> PageResponse:
        """Get multiple records with pagination."""
        total = await self.count()
        offset = (page - 1) * page_size
        statement = select(self.model).offset(offset).limit(page_size)
        result = await self.db_session.execute(statement)
        items = list(result.scalars().all())
        return PageResponse.create(
            items=items, total=total, page=page, page_size=page_size
        )

    async def update(
        self, record_id: uuid.UUID, obj_in: UpdateSchemaType
    ) -> ModelType | None:
        """Update a record with only the fields provided in the schema."""
        db_obj = await self.get(record_id)
        if not db_obj:
            return None

        for field, value in obj_in.model_dump(exclude_unset=True).items():
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
        statement = select(func.count()).select_from(self.model)
        result = await self.db_session.execute(statement)
        return result.scalar_one() or 0

    async def exists(self, record_id: uuid.UUID) -> bool:
        """Check if a record exists."""
        return await self.get(record_id) is not None
