"""Batch service — upload handling, video creation, and counter management."""

import logging
import uuid
from pathlib import PurePosixPath
from typing import Annotated

from fastapi import Depends

from api.batches.crud import BatchCrudDep
from api.batches.models.batch import Batch
from api.batches.schemas import BatchCreate, BatchProgressEvent, BatchRead
from api.constants import UPLOAD_CONTENT_TYPES
from api.deps.celery import celery_app
from api.events.schemas import EventChannel
from api.events.service import EventService
from api.storage import StorageDep
from api.videos.crud import VideoCrud
from api.videos.enums import VideoStatus
from api.videos.models.video import Video

logger = logging.getLogger(__name__)


class BatchService:
    """Handles batch uploads, video creation, and counter updates."""

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
    ) -> BatchRead:
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
            logger.exception("Batch %s: R2 upload failed", batch_id)
            await self.crud.delete(batch_id)
            raise

        await self.crud.update_file_key(batch_id, file_key)

        celery_app.send_task("api.batches.tasks.process_batch", args=[str(batch_id)])
        logger.info("Batch %s: dispatched processing task", batch_id)

        batch = await self.crud.get(batch_id)
        return BatchRead.model_validate(batch)

    # ------------------------------------------------------------------
    # Video creation
    # ------------------------------------------------------------------

    async def create_batch_videos(
        self, batch: Batch, videos: list[Video]
    ) -> list[Video]:
        """Create videos for a batch and update batch counters."""
        video_crud = VideoCrud(self.crud.db_session)
        await video_crud.create_bulk(videos)

        pending = sum(1 for video in videos if video.status == VideoStatus.processing)
        batch.total_videos = len(videos)
        batch.pending_count = pending
        batch.failed_count = len(videos) - pending
        await self.crud.db_session.commit()

        return videos

    # ------------------------------------------------------------------
    # Counter updates
    # ------------------------------------------------------------------

    async def recompute_counters(self, batch_id: uuid.UUID) -> Batch | None:
        """Recompute batch counters and costs from its videos.

        Returns the updated batch, or None if it no longer exists.
        """
        batch = await self.crud.get(batch_id)
        if not batch:
            logger.warning("Batch %s not found (deleted?)", batch_id)
            return None

        video_crud = VideoCrud(self.crud.db_session)

        counts = await video_crud.get_status_counts_by_batch(batch_id)
        batch.completed_count = counts.finished
        batch.failed_count = counts.failed
        batch.pending_count = counts.processing

        totals = await video_crud.get_cost_totals_by_batch(batch_id)
        batch.duration_ms = totals.duration_ms
        batch.tts_cost_usd = totals.tts.cost_usd
        batch.tts_token_count = totals.tts.token_count
        batch.segmentation_cost_usd = totals.segmentation.cost_usd
        batch.segmentation_token_count = totals.segmentation.token_count
        batch.image_generation_cost_usd = totals.image_generation.cost_usd
        batch.image_generation_token_count = totals.image_generation.token_count
        batch.total_cost_usd = totals.total.cost_usd
        batch.total_token_count = totals.total.token_count

        batch.status = batch.derive_status().value
        await self.crud.db_session.commit()

        logger.info(
            "Batch %s: completed=%d failed=%d pending=%d total=%d → %s",
            batch_id,
            batch.completed_count,
            batch.failed_count,
            batch.pending_count,
            batch.total_videos,
            batch.status,
        )
        return batch

    async def emit_progress(self, events: EventService, batch: Batch) -> None:
        """Emit a batch progress SSE event. Failures are logged, never raised."""
        try:
            channel = EventChannel.batch.value.format(batch_id=batch.id)
            await events.emit(
                channel, BatchProgressEvent(batch_id=str(batch.id), status=batch.status)
            )
        except Exception:
            logger.warning(
                "Batch %s: failed to emit SSE event", batch.id, exc_info=True
            )


BatchServiceDep = Annotated[BatchService, Depends()]
