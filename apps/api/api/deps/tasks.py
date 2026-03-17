"""Scheduled Celery tasks — retention cleanup and stale task recovery."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from api.batches.crud import BatchCrud
from api.batches.models.batch import Batch
from api.batches.service import BatchService
from api.deps.celery import async_task, celery_app, task_context
from api.settings_module.crud import AppSettingsCrud
from api.videos.enums import VideoStatus
from api.videos.models.video import Video

logger = logging.getLogger(__name__)

# Time after which a "processing" video is considered stuck (killed by deploy).
# Must be longer than the slowest pipeline stage (assembly can take 10+ minutes).
STALE_PROCESSING_MINUTES = 60


@async_task(celery_app, bind=True)
async def recover_stale_videos(self) -> int:
    """Mark videos stuck in 'processing' as failed.

    Runs on worker startup. Catches videos abandoned by a killed worker
    (e.g. during deployment). Uses updated_at to detect staleness.
    """
    async with task_context() as ctx:
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=STALE_PROCESSING_MINUTES
        )

        # Find affected batch IDs before updating
        stale_batch_ids_result = await ctx.session.execute(
            select(Video.batch_id)
            .where(
                Video.status == VideoStatus.processing,
                Video.updated_at < cutoff,
                Video.batch_id.is_not(None),
            )
            .distinct()
        )
        affected_batch_ids = [row[0] for row in stale_batch_ids_result.all()]

        # Mark stale videos as failed
        result = await ctx.session.execute(
            update(Video)
            .where(
                Video.status == VideoStatus.processing,
                Video.updated_at < cutoff,
            )
            .values(
                status=VideoStatus.failed,
                error_message="Interrupted — worker was restarted during processing",
            )
        )
        await ctx.session.commit()

        recovered_count = result.rowcount
        if recovered_count:
            logger.info("Recovered %d stale processing videos", recovered_count)

        # Recompute batch counters for affected batches
        if affected_batch_ids:
            batch_service = BatchService(BatchCrud(ctx.session), ctx.storage)
            for batch_id in affected_batch_ids:
                try:
                    batch = await batch_service.recompute_counters(batch_id)
                    if batch:
                        await batch_service.emit_progress(ctx.events, batch)
                except Exception:
                    logger.exception(
                        "Failed to update batch %s after stale recovery", batch_id
                    )

        return recovered_count


@async_task(celery_app, bind=True)
async def cleanup_expired_videos(self) -> dict[str, int]:
    """Delete videos and batches that exceed the retention period.

    Runs daily via Celery Beat. Reads retention_days from app settings.
    Deletes S3 artifacts and database records for expired finished videos,
    then removes empty batches.
    """
    async with task_context() as ctx:
        app_settings = await AppSettingsCrud(ctx.session).get()
        retention_days = app_settings.retention_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        logger.info(
            "Retention cleanup starting (retention=%d days, cutoff=%s)",
            retention_days,
            cutoff.isoformat(),
        )

        # Find expired finished videos
        expired_videos_stmt = select(Video).where(
            Video.status == VideoStatus.finished,
            Video.created_at < cutoff,
        )
        result = await ctx.session.execute(expired_videos_stmt)
        expired_videos = list(result.scalars().all())

        deleted_videos = 0
        for video in expired_videos:
            try:
                ctx.storage.delete_prefix(f"{video.s3_prefix}/")
                await ctx.session.delete(video)
                deleted_videos += 1
            except Exception:
                logger.exception("Failed to delete video %s", video.id)

        # Find expired failed videos (no S3 artifacts to clean)
        expired_failed_stmt = select(Video).where(
            Video.status == VideoStatus.failed,
            Video.created_at < cutoff,
        )
        result = await ctx.session.execute(expired_failed_stmt)
        expired_failed = list(result.scalars().all())

        for video in expired_failed:
            try:
                await ctx.session.delete(video)
                deleted_videos += 1
            except Exception:
                logger.exception("Failed to delete failed video %s", video.id)

        await ctx.session.commit()

        # Clean up empty batches (batches with no remaining videos)
        empty_batches_stmt = select(Batch).where(~Batch.videos.any())
        result = await ctx.session.execute(empty_batches_stmt)
        empty_batches = list(result.scalars().all())

        deleted_batches = 0
        for batch in empty_batches:
            try:
                await ctx.session.delete(batch)
                deleted_batches += 1
            except Exception:
                logger.exception("Failed to delete empty batch %s", batch.id)

        await ctx.session.commit()

        logger.info(
            "Retention cleanup complete (deleted %d videos, %d batches)",
            deleted_videos,
            deleted_batches,
        )
        return {"deleted_videos": deleted_videos, "deleted_batches": deleted_batches}
