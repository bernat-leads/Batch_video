"""Celery task — thin wrapper that builds VideoService and runs the pipeline."""

import logging
import uuid

from api.batches.crud import BatchCrud
from api.batches.service import BatchService
from api.deps.celery import async_task, celery_app, task_context
from api.settings_module.crud import AppSettingsCrud
from api.shots.service import ShotService
from api.videos.pipeline.image_generation import GeminiImageGenService
from api.videos.pipeline.segmentation import ClaudeSegmentationService
from api.videos.pipeline.tts import OpenAITTSService
from api.videos.pipeline.video_editor import MoviePyTikTokAdTemplate
from api.videos.schemas import VideoCreate, VideoGenerationResult
from api.videos.service import VideoService

logger = logging.getLogger(__name__)


@async_task(celery_app, bind=True, max_retries=0)
async def process_video(
    self,
    video_input_data: dict,
    batch_id: str | None = None,
    video_id: str = "",
) -> VideoGenerationResult:
    """Process a single video through the full pipeline."""
    video_input = VideoCreate.model_validate(video_input_data)
    logger.info("Task started (batch=%s, video=%s)", batch_id, video_id)

    async with task_context() as ctx:
        service = VideoService(
            session=ctx.session,
            storage=ctx.storage,
            events=ctx.events,
            app_settings=AppSettingsCrud(ctx.session),
            tts=OpenAITTSService(ctx.storage),
            segmentation=ClaudeSegmentationService(),
            shots=ShotService(ctx.session, ctx.storage, GeminiImageGenService()),
            video_template=MoviePyTikTokAdTemplate(),
        )

        try:
            result = await service.generate_video(
                video_id=uuid.UUID(video_id),
                video_input=video_input,
            )
            logger.info(
                "Task complete (video=%s, cost=$%.4f)",
                result.video_id,
                result.total.cost_usd,
            )
            return result
        except Exception:
            logger.exception("Task failed (batch=%s, video=%s)", batch_id, video_id)
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
