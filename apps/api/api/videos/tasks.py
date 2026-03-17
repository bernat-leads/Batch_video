"""Celery task — thin wrapper that builds VideoService and runs the pipeline."""

import logging
import uuid

from api.batches.crud import BatchCrud
from api.batches.service import BatchService
from api.deps.celery import async_task, celery_app, task_context
from api.settings_module.crud import AppSettingsCrud
from api.videos.pipeline.image_generation import GeminiImageGenService
from api.videos.pipeline.segmentation import ClaudeSegmentationService
from api.videos.pipeline.tts import OpenAITTSService
from api.videos.crud import VideoCrud
from api.videos.pipeline.video_editor import MoviePyVideoEditor
from api.videos.pipeline.video_editor.effects import NumpyEffectService
from api.videos.pipeline.video_editor.templates import TIKTOK_AD_TEMPLATE
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.events.schemas import EventChannel
from api.videos.models.video import Video
from api.videos.schemas import VideoCreate, VideoGenerationResult, VideoProgressEvent
from api.videos.service import VideoService
from api.videos.pipeline.tts.elevenlabs import ElevenLabsTTSService

logger = logging.getLogger(__name__)


def _build_service(ctx) -> VideoService:
    """Build a VideoService from task context."""
    return VideoService(
        session=ctx.session,
        storage=ctx.storage,
        events=ctx.events,
        app_settings=AppSettingsCrud(ctx.session),
        video_crud=VideoCrud(ctx.session),
        tts=ElevenLabsTTSService(),
        segmentation=ClaudeSegmentationService(),
        image_gen=GeminiImageGenService(),
        editor=MoviePyVideoEditor(NumpyEffectService()),
    )


@async_task(celery_app, bind=True, max_retries=0)
async def process_video(
    self,
    video_input_data: dict,
    batch_id: str | None = None,
) -> VideoGenerationResult:
    """Process a single video through the full pipeline."""
    video_input = VideoCreate.model_validate(video_input_data)
    if batch_id:
        video_input.batch_id = uuid.UUID(batch_id)
    logger.info("Task started (batch=%s)", batch_id)

    async with task_context() as ctx:
        service = _build_service(ctx)

        try:
            result = await service.generate_video(
                video_input=video_input,
                template=TIKTOK_AD_TEMPLATE,
            )
            logger.info(
                "Task complete (video=%s, cost=$%.4f)",
                result.video_id,
                result.total.cost_usd,
            )
            return result
        except Exception:
            logger.exception("Task failed (batch=%s)", batch_id)
            raise
        finally:
            if batch_id:
                try:
                    batch_service = BatchService(BatchCrud(ctx.session), ctx.storage)
                    batch = await batch_service.recompute_counters(uuid.UUID(batch_id))
                    if batch:
                        await batch_service.emit_progress(ctx.events, batch)
                except Exception:
                    logger.exception(
                        "Failed to update batch counters (batch=%s)", batch_id
                    )


@async_task(celery_app, bind=True, max_retries=0)
async def retry_video(self, video_id: str) -> VideoGenerationResult:
    """Retry a failed video from the stage that failed."""
    logger.info("Retry task started (video=%s)", video_id)

    async with task_context() as ctx:
        service = _build_service(ctx)
        # Eagerly load shots — lazy load fails in async context (greenlet error)
        result = await ctx.session.execute(
            select(Video)
            .options(selectinload(Video.shots))
            .where(Video.id == uuid.UUID(video_id))
        )
        video = result.scalars().first()
        if not video:
            raise ValueError(f"Video {video_id} not found")

        # Set video to processing and emit events immediately
        video.status = "processing"
        video.error_message = None
        await ctx.session.commit()

        try:
            event = VideoProgressEvent(
                video_id=str(video.id),
                batch_id=str(video.batch_id) if video.batch_id else None,
                status=video.status,
                stage=video.current_stage,
            )
            channel = EventChannel.video.value.format(video_id=video.id)
            await ctx.events.emit(channel, event)
        except Exception:
            logger.debug("Failed to emit video event (video=%s)", video_id)

        if video.batch_id:
            try:
                batch_service = BatchService(BatchCrud(ctx.session), ctx.storage)
                batch = await batch_service.recompute_counters(video.batch_id)
                if batch:
                    await batch_service.emit_progress(ctx.events, batch)
            except Exception:
                logger.exception(
                    "Failed to update batch counters at retry start (batch=%s)",
                    video.batch_id,
                )

        try:
            result = await service.retry_video(
                video=video,
                template=TIKTOK_AD_TEMPLATE,
            )
            logger.info(
                "Retry complete (video=%s, cost=$%.4f)",
                result.video_id,
                result.total.cost_usd,
            )
            return result
        except Exception:
            logger.exception("Retry failed (video=%s)", video_id)
            raise
        finally:
            if video.batch_id:
                try:
                    batch_service = BatchService(BatchCrud(ctx.session), ctx.storage)
                    batch = await batch_service.recompute_counters(video.batch_id)
                    if batch:
                        await batch_service.emit_progress(ctx.events, batch)
                except Exception:
                    logger.exception(
                        "Failed to update batch counters (batch=%s)", video.batch_id
                    )
