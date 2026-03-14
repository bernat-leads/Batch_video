"""Batch CRUD operations."""

import uuid
from typing import Annotated

from fastapi import Depends

from api.batches.models.batch import Batch
from api.batches.parser import VideoRowData
from api.batches.schemas import BatchRead, BatchUpdate
from api.core.crud import BaseCrud
from api.deps.db import SessionDep, save
from api.videos.enums import VideoStage, VideoStatus
from api.videos.models.video import Video


class BatchCrud(BaseCrud[Batch, BatchUpdate, BatchUpdate]):
    """CRUD operations for batches."""

    def __init__(self, session: SessionDep) -> None:
        super().__init__(session=session, model=Batch)

    async def create_from_upload(
        self,
        batch_name: str,
        column_mapping: dict,
        file_name: str,
        file_key: str,
    ) -> Batch:
        """Create a batch record for file-based upload (videos added later by Celery)."""
        batch = Batch(
            name=batch_name,
            total_videos=0,
            column_mapping=column_mapping,
            file_name=file_name,
            file_key=file_key,
        )
        await save(self.db_session, batch)
        return batch

    async def update_file_key(self, batch_id: uuid.UUID, file_key: str) -> None:
        """Update the R2 file key after upload (replaces placeholder set at creation)."""
        batch = await self.get(batch_id)
        if batch:
            batch.file_key = file_key
            await self.db_session.commit()

    async def set_batch_error(self, batch_id: uuid.UUID, error_message: str) -> None:
        """Set error message on batch (batch-level parsing failure)."""
        batch = await self.get(batch_id)
        if batch:
            batch.error_message = error_message
            await self.db_session.commit()

    async def create_videos_bulk(
        self,
        batch_id: uuid.UUID,
        rows: list[VideoRowData],
    ) -> int:
        """Create video records in bulk from parsed row data."""
        batch = await self.get(batch_id)
        if not batch:
            msg = f"Batch {batch_id} not found"
            raise ValueError(msg)

        pending_count = 0
        failed_count = 0

        for row in rows:
            if row.is_valid:
                pending_count += 1
            else:
                failed_count += 1
            self.db_session.add(Video(
                batch_id=batch_id,
                script_text=row.script_text,
                voice_id=row.voice_id,
                style=row.style,
                top_text=row.top_text,
                prompt=row.prompt,
                status=VideoStatus.failed if not row.is_valid else VideoStatus.pending,
                current_stage=VideoStage.queued,
                error_message=row.error_message,
            ))

        batch.total_videos = len(rows)
        batch.pending_count = pending_count
        batch.failed_count = failed_count
        await self.db_session.commit()
        return len(rows)

    async def get_as_schema(self, batch_id: uuid.UUID) -> BatchRead | None:
        """Get a single batch as a Pydantic schema."""
        batch = await self.get(batch_id)
        if not batch:
            return None
        return BatchRead.model_validate(batch)


BatchCrudDep = Annotated[BatchCrud, Depends()]
