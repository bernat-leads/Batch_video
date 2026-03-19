"""Celery tasks for batch processing."""

import logging
import uuid

from api.batches.crud import BatchCrud
from api.batches.schemas import BatchProcessResult, BatchProgressEvent
from api.batches.service import BatchService
from api.core.exceptions import BatchParseError
from api.deps.celery import async_task, celery_app, task_context
from api.deps.storage import s3_client
from api.events.schemas import EventChannel
from api.parser import FieldDef, PandasFileParser
from api.storage import StorageService
from api.videos.models.video import Video
from api.videos.schemas import VideoCreate
from api.videos.tasks import process_video

logger = logging.getLogger(__name__)

VIDEO_FIELDS: tuple[FieldDef, ...] = (
    FieldDef(name="script_text", required=True),
    FieldDef(name="voice_id"),
    FieldDef(name="style"),
    FieldDef(name="top_text"),
    FieldDef(name="file_name"),
)


@celery_app.task(bind=True, max_retries=2)
def cleanup_batch_files(self, batch_id: str) -> None:
    """Delete all S3 files under batches/{batch_id}/."""
    storage = StorageService(s3_client)
    deleted = storage.delete_prefix(f"batches/{batch_id}/")
    logger.info("Batch %s: deleted %d files from S3", batch_id, deleted)


@async_task(celery_app, bind=True, max_retries=2)
async def process_batch(self, batch_id: str) -> BatchProcessResult:
    """Parse uploaded Excel/CSV file, create video records, dispatch pipeline tasks."""
    batch_uuid = uuid.UUID(batch_id)

    async with task_context() as ctx:
        crud = BatchCrud(ctx.session)
        service = BatchService(crud, ctx.storage)
        batch = await crud.get(batch_uuid)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        try:
            file_bytes = ctx.storage.download_file(batch.file_key)
            parser = PandasFileParser(
                file_bytes=file_bytes,
                file_name=batch.file_name or "",
                column_mapping=batch.column_mapping or {},
                fields=VIDEO_FIELDS,
            )
            rows = parser.parse()

            if not rows:
                await crud.set_batch_error(batch.id, "No rows found in file")
                return BatchProcessResult(batch_id=batch_id, error="empty file")

            failed_videos = [
                Video.from_parsed_row(row, batch_uuid)
                for row in rows
                if not row.is_valid
            ]
            valid_rows = [row for row in rows if row.is_valid]

            if failed_videos:
                await service.create_batch_videos(batch, failed_videos)

            await ctx.session.commit()

            dispatched = 0
            for row in valid_rows:
                process_video.delay(
                    VideoCreate(
                        script_text=row.data["script_text"],
                        voice_id=row.data.get("voice_id") or None,
                        style=row.data.get("style") or None,
                        top_text=row.data.get("top_text") or None,
                        file_name=row.data.get("file_name") or None,
                    ).model_dump(),
                    batch_id=batch_id,
                )
                dispatched += 1

            try:
                channel = EventChannel.batch.value.format(batch_id=batch_id)
                status = "processing" if dispatched else "failed"
                await ctx.events.emit(
                    channel, BatchProgressEvent(batch_id=batch_id, status=status)
                )
            except Exception:
                logger.debug(
                    "Batch %s: failed to emit SSE event", batch_id, exc_info=True
                )

            logger.info(
                "Batch %s: dispatched %d tasks (%d failed)",
                batch_id,
                dispatched,
                len(failed_videos),
            )
            return BatchProcessResult(batch_id=batch_id, videos_created=len(rows))

        except (ValueError, BatchParseError) as e:
            logger.warning("Batch %s: parse error — %s", batch_id, e)
            await crud.set_batch_error(batch.id, str(e))
            return BatchProcessResult(batch_id=batch_id, error=str(e))
        except Exception as e:
            logger.exception("Batch %s: unexpected error", batch_id)
            await crud.set_batch_error(batch.id, f"Processing failed: {e}")
            return BatchProcessResult(batch_id=batch_id, error=str(e))
