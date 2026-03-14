"""Celery tasks for batch processing."""

import asyncio
import logging
import uuid

from api.batches.crud import BatchCrud
from api.batches.parser import BatchFileParser
from api.deps.celery import celery_app
from api.deps.db import async_session_factory
from api.deps.storage import StorageService
from api.shots.models.shot import Shot
from api.videos.models.video import Video

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def cleanup_batch_files(self, batch_id: str) -> dict:
    """Delete all R2 files under batches/{batch_id}/."""
    storage = StorageService()
    prefix = f"batches/{batch_id}/"
    deleted = storage.delete_prefix(prefix)
    logger.info("Batch %s: deleted %d files from R2", batch_id, deleted)
    return {"batch_id": batch_id, "files_deleted": deleted}


@celery_app.task(bind=True, max_retries=2)
def process_batch(self, batch_id: str) -> dict:
    """Parse uploaded Excel/CSV file and create video records."""
    return asyncio.run(_process_batch(batch_id))


async def _process_batch(batch_id: str) -> dict:

    storage = StorageService()
    batch_uuid = uuid.UUID(batch_id)

    async with async_session_factory() as session:
        crud = BatchCrud(session)
        batch = await crud.get(batch_uuid)
        if not batch:
            msg = f"Batch {batch_id} not found"
            raise ValueError(msg)

        try:
            file_bytes = storage.download_file(batch.file_key)

            parser = BatchFileParser(
                file_bytes=file_bytes,
                file_name=batch.file_name or "",
                column_mapping=batch.column_mapping or {},
            )
            rows = parser.parse()

            if not rows:
                await crud.set_batch_error(batch.id, "No rows found in file")
                return {"batch_id": batch_id, "error": "empty file"}

            count = await crud.create_videos_bulk(batch_uuid, rows)
            logger.info("Batch %s: created %d videos from %s", batch_id, count, batch.file_name)
            return {"batch_id": batch_id, "videos_created": count}

        except ValueError as e:
            await crud.set_batch_error(batch.id, str(e))
            return {"batch_id": batch_id, "error": str(e)}
        except Exception as e:
            logger.exception("Batch %s: unexpected error", batch_id)
            await crud.set_batch_error(batch.id, f"Processing failed: {e}")
            return {"batch_id": batch_id, "error": str(e)}
