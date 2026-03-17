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
from api.videos.pipeline.video_editor.templates import TIKTOK_AD_TEMPLATE
from api.videos.schemas import VideoCreate, VideoGenerationResult
from api.videos.service import VideoService
from api.videos.pipeline.tts.elevenlabs import ElevenLabsTTSService

logger = logging.getLogger(__name__)


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
        service = VideoService(
            session=ctx.session,
            storage=ctx.storage,
            events=ctx.events,
            app_settings=AppSettingsCrud(ctx.session),
            video_crud=VideoCrud(ctx.session),
            tts=ElevenLabsTTSService(),
            segmentation=ClaudeSegmentationService(),
            image_gen=GeminiImageGenService(),
            editor=MoviePyVideoEditor(),
        )

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
