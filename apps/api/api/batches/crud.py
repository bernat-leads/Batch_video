"""Batch CRUD operations."""

import uuid
from typing import Annotated

from fastapi import Depends

from api.batches.models.batch import Batch
from api.batches.schemas import BatchCreate, BatchUpdate
from api.core.crud import BaseCrud
from api.deps.db import SessionDep


class BatchCrud(BaseCrud[Batch, BatchCreate, BatchUpdate]):
    """CRUD operations for batches."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Batch)

    async def update_file_key(self, batch_id: uuid.UUID, file_key: str) -> None:
        """Update the R2 file key after upload."""
        batch = await self.get(batch_id)
        if batch:
            batch.file_key = file_key
            await self.db_session.commit()

    async def set_batch_error(self, batch_id: uuid.UUID, error_message: str) -> None:
        """Set error message on batch."""
        batch = await self.get(batch_id)
        if batch:
            batch.error_message = error_message
            await self.db_session.commit()


BatchCrudDep = Annotated[BatchCrud, Depends()]
