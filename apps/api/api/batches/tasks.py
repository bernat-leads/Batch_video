"""Celery tasks for batch processing."""

import logging
import uuid

from api.batches.crud import BatchCrud
from api.batches.enums import BatchStatus
from api.batches.schemas import BatchProcessResult, BatchProgressEvent
from api.batches.service import BatchService
from api.core.exceptions import BatchParseError
from api.deps.celery import async_task, celery_app, task_context
from api.deps.storage import s3_client
from api.events.schemas import EventChannel
from api.parser import FieldDef, PandasFileParser
from api.storage import StorageService
from api.videos.enums import VideoStatus
from api.videos.models.video import Video
from api.videos.schemas import VideoCreate
from api.videos.tasks import process_video

logger = logging.getLogger(__name__)

VIDEO_FIELDS: tuple[FieldDef, ...] = (
    FieldDef(name="script_text", required=True),
    FieldDef(name="voice_id"),
    FieldDef(name="style"),
    FieldDef(name="top_text"),
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
                batch.status = BatchStatus.failed.value
                await crud.set_batch_error(batch.id, "No rows found in file")
                return BatchProcessResult(batch_id=batch_id, error="empty file")

            videos = await service.create_batch_videos(
                batch,
                [Video.from_parsed_row(row, batch_uuid) for row in rows],
            )
            dispatched = 0
            failed_count = 0

            for video in videos:
                if video.status != VideoStatus.processing:
                    failed_count += 1
                    continue
                process_video.delay(
                    VideoCreate(
                        script_text=video.script_text,
                        voice_id=video.voice_id,
                        style=video.style,
                        top_text=video.top_text,
                    ).model_dump(),
                    batch_id=batch_id,
                    video_id=str(video.id),
                )
                dispatched += 1

            batch.status = (
                BatchStatus.processing.value if dispatched else BatchStatus.failed.value
            )

            try:
                channel = EventChannel.batch.value.format(batch_id=batch_id)
                await ctx.events.emit(
                    channel, BatchProgressEvent(batch_id=batch_id, status=batch.status)
                )
            except Exception:
                logger.debug(
                    "Batch %s: failed to emit SSE event", batch_id, exc_info=True
                )

            logger.info(
                "Batch %s: dispatched %d tasks (%d failed)",
                batch_id,
                dispatched,
                failed_count,
            )
            return BatchProcessResult(batch_id=batch_id, videos_created=len(videos))

        except (ValueError, BatchParseError) as e:
            logger.warning("Batch %s: parse error — %s", batch_id, e)
            batch.status = BatchStatus.failed.value
            await crud.set_batch_error(batch.id, str(e))
            return BatchProcessResult(batch_id=batch_id, error=str(e))
        except Exception as e:
            logger.exception("Batch %s: unexpected error", batch_id)
            batch.status = BatchStatus.failed.value
            await crud.set_batch_error(batch.id, f"Processing failed: {e}")
            return BatchProcessResult(batch_id=batch_id, error=str(e))
