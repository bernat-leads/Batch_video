"""Scheduled Celery tasks — retention cleanup."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from api.batches.models.batch import Batch
from api.deps.celery import async_task, celery_app, task_context
from api.settings_module.crud import AppSettingsCrud
from api.videos.enums import VideoStatus
from api.videos.models.video import Video

logger = logging.getLogger(__name__)


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
