"""Batch service — upload handling and video creation."""

import logging
import uuid
from pathlib import PurePosixPath
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.batches.crud import BatchCrud, BatchCrudDep
from api.batches.models.batch import Batch
from api.batches.schemas import BatchCreate, BatchProgressEvent
from api.constants import UPLOAD_CONTENT_TYPES
from api.deps.celery import celery_app
from api.events.schemas import EventChannel
from api.events.service import EventService
from api.storage import StorageDep, StorageService
from api.videos.crud import VideoCrud
from api.videos.models.video import Video

logger = logging.getLogger(__name__)


class BatchService:
    """Handles batch uploads and video creation."""

    def __init__(self, crud: BatchCrudDep, storage: StorageDep) -> None:
        """Initialize with batch CRUD and storage dependencies."""
        self.crud = crud
        self.storage = storage

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    async def create_batch(
        self,
        contents: bytes,
        file_name: str,
        batch_name: str,
        column_mapping: dict,
    ) -> Batch:
        """Store file in R2, create batch record, and launch background processing."""
        ext = PurePosixPath(file_name).suffix.lower()

        batch = await self.crud.create(
            BatchCreate(
                name=batch_name,
                column_mapping=column_mapping,
                file_name=file_name,
                file_key=f"batches/pending{ext}",
            )
        )
        batch_id = batch.id
        logger.info("Batch %s: created '%s' from '%s'", batch_id, batch_name, file_name)

        file_key = f"batches/{batch_id}/original{ext}"
        content_type = UPLOAD_CONTENT_TYPES.get(ext, "application/octet-stream")

        try:
            self.storage.upload_file(file_key, contents, content_type)
        except Exception:
            logger.exception("Batch %s: S3 upload failed", batch_id)
            await self.crud.delete(batch_id)
            raise

        await self.crud.update_file_key(batch_id, file_key)

        celery_app.send_task("api.batches.tasks.process_batch", args=[str(batch_id)])
        logger.info("Batch %s: dispatched processing task", batch_id)

        batch = await self.crud.get(batch_id)
        return batch

    # ------------------------------------------------------------------
    # Video creation
    # ------------------------------------------------------------------

    async def create_batch_videos(
        self, batch: Batch, videos: list[Video]
    ) -> list[Video]:
        """Create videos for a batch."""
        video_crud = VideoCrud(self.crud.db_session)
        await video_crud.create_bulk(videos)
        return videos

    # ------------------------------------------------------------------
    # SSE
    # ------------------------------------------------------------------

    async def emit_progress(self, events: EventService, batch: Batch) -> None:
        """Emit a batch progress SSE event. Failures are logged, never raised."""
        try:
            channel = EventChannel.batch.value.format(batch_id=batch.id)
            # Refresh to get live computed status
            await self.crud.db_session.refresh(batch)
            await events.emit(
                channel,
                BatchProgressEvent(batch_id=str(batch.id), status=batch.status),
            )
        except Exception:
            logger.warning(
                "Batch %s: failed to emit SSE event", batch.id, exc_info=True
            )


BatchServiceDep = Annotated[BatchService, Depends()]


async def emit_batch_progress(
    session: AsyncSession,
    storage: StorageService,
    events: EventService,
    batch_id: uuid.UUID,
) -> None:
    """Emit batch progress SSE. Safe to call from any task."""
    crud = BatchCrud(session)
    batch = await crud.get(batch_id)
    if batch:
        service = BatchService(crud, storage)
        await service.emit_progress(events, batch)
