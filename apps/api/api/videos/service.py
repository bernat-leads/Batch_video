"""Video generation service — orchestrates the full pipeline."""

import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import SegmentationEmptyError
from api.core.schemas import AICost
from api.events.schemas import EventChannel
from api.events.service import EventService
from api.settings_module.crud import AppSettingsCrud
from api.shots.models.shot import Shot
from api.storage import StorageService
from api.videos.crud import VideoCrud
from api.videos.enums import VideoStage, VideoStatus
from api.videos.models.video import Video
from api.videos.pipeline.image_generation import ImageGenService
from api.videos.pipeline.image_generation.schemas import ImageConfig
from api.videos.pipeline.segmentation import SegmentationService
from api.videos.pipeline.segmentation.schemas import (
    SegmentationInput,
    SegmentationResult,
    SegmentResult,
)
from api.videos.pipeline.tts import TTSService
from api.videos.pipeline.tts.schemas import TTSInput, TTSResult
from api.videos.pipeline.video_editor import (
    EditResult,
    Segment,
    VideoEditor,
    VideoTemplate,
)
from api.videos.pipeline.video_editor.schemas import AssemblyInput
from api.videos.schemas import VideoCreate, VideoGenerationResult, VideoProgressEvent

logger = logging.getLogger(__name__)


class VideoService:
    """Orchestrates the full video generation pipeline."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        events: EventService,
        app_settings: AppSettingsCrud,
        video_crud: VideoCrud,
        tts: TTSService,
        segmentation: SegmentationService,
        image_gen: ImageGenService,
        editor: VideoEditor,
    ) -> None:
        """Initialize with pipeline dependencies."""
        self._session = session
        self._storage = storage
        self._events = events
        self._app_settings = app_settings
        self._video_crud = video_crud
        self._tts = tts
        self._segmentation = segmentation
        self._image_gen = image_gen
        self._editor = editor

    async def generate_video(
        self,
        video_input: VideoCreate,
        template: VideoTemplate,
    ) -> VideoGenerationResult:
        """Create a video record and run the full pipeline.

        On failure, marks the video as failed and cleans up partial S3 artifacts.
        """
        video_input.prompt = await self._resolve_prompt(video_input)
        video = await self._video_crud.create(video_input)
        await self._emit_progress(video)

        try:
            return await self._run_pipeline(video, template)
        except Exception as error:
            await self._handle_failure(video, error)
            raise

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    async def _run_pipeline(
        self,
        video: Video,
        template: VideoTemplate,
    ) -> VideoGenerationResult:
        """Execute all pipeline stages and persist the final result."""
        tts_result = await self._run_tts(video)
        seg_result = await self._run_segmentation(video, tts_result, template)
        shots = await self._run_image_generation(video, seg_result, template)
        edit_result = await self._run_assembly(video, shots, tts_result, template)
        await self._run_upload(video, edit_result)
        return await self._finalize(
            video, edit_result, tts_result.cost, seg_result.cost
        )

    async def _run_tts(self, video: Video) -> TTSResult:
        """Stage 1: Convert script to speech, upload audio to S3."""
        await self._update_stage(video, VideoStage.tts)
        tts_input = TTSInput(
            script_text=video.script_text,
            voice_id=video.voice_id,
        )
        tts_result = await asyncio.to_thread(self._tts.synthesize, tts_input)

        self._storage.upload_file(
            video.audio_s3_key, tts_result.audio_bytes, tts_result.content_type
        )
        video.audio_url = video.audio_s3_key
        return tts_result

    async def _run_segmentation(
        self, video: Video, tts_result: TTSResult, template: VideoTemplate
    ) -> SegmentationResult:
        """Stage 2: Segment script into visual chunks with image prompts."""
        await self._update_stage(video, VideoStage.segmentation)
        seg_input = SegmentationInput(
            script_text=video.script_text,
            word_timestamps=tts_result.word_timestamps,
            style=video.style,
            prompt=video.prompt,
            template_context=template.template_context,
        )
        seg_result = await self._segmentation.segment_script(seg_input)
        if not seg_result.segments:
            raise SegmentationEmptyError()
        return seg_result

    async def _run_image_generation(
        self, video: Video, seg_result: SegmentationResult, template: VideoTemplate
    ) -> list[Shot]:
        """Stage 3: Generate images in parallel, upload to S3, create shot records."""
        await self._update_stage(video, VideoStage.image_generation)

        tasks = [
            asyncio.to_thread(
                self._generate_shot, video, segment, template.image_config
            )
            for segment in seg_result.segments
        ]
        shots = await asyncio.gather(*tasks)

        for shot in shots:
            self._session.add(shot)
        await self._session.flush()
        return list(shots)

    def _generate_shot(
        self, video: Video, segment: SegmentResult, image_config: ImageConfig
    ) -> Shot:
        """Generate image, upload to S3, and build Shot object (runs in thread)."""
        image_result = self._image_gen.generate_image(
            segment.image_prompt, image_config
        )

        s3_key = video.shot_s3_key(segment.order)
        self._storage.upload_file(
            s3_key, image_result.image_bytes, image_result.content_type
        )

        shot = Shot(
            video_id=video.id,
            order=segment.order,
            text=segment.text,
            image_prompt=segment.image_prompt,
            effect_config=segment.effect.model_dump(),
            start_time=segment.start_time,
            end_time=segment.end_time,
            image_url=s3_key,
            cost_usd=image_result.cost.cost_usd,
        )
        shot.image_bytes = image_result.image_bytes  # transient — used by assembly
        return shot

    async def _run_assembly(
        self,
        video: Video,
        shots: list[Shot],
        tts_result: TTSResult,
        template: VideoTemplate,
    ) -> EditResult:
        """Stage 4: Assemble final video from cached shot images and TTS audio."""
        await self._update_stage(video, VideoStage.assembly)

        assembly_input = AssemblyInput(
            template=template,
            segments=[
                Segment(
                    image_bytes=shot.image_bytes,
                    duration=shot.end_time - shot.start_time,
                    effect=shot.effect_config,
                )
                for shot in shots
            ],
            audio_bytes=tts_result.audio_bytes,
            word_timestamps=tts_result.word_timestamps,
            top_text=video.top_text,
        )

        return await asyncio.to_thread(self._editor.assemble_video, assembly_input)

    async def _run_upload(self, video: Video, edit_result: EditResult) -> None:
        """Stage 5: Upload the rendered video to S3."""
        await self._update_stage(video, VideoStage.upload)
        self._storage.upload_file(
            video.output_s3_key, edit_result.video_bytes, "video/mp4"
        )
        video.output_url = video.output_s3_key
        video.duration_ms = edit_result.duration_ms
        video.file_size_bytes = len(edit_result.video_bytes)

    async def _finalize(
        self,
        video: Video,
        edit_result: EditResult,
        tts_cost: AICost,
        seg_cost: AICost,
    ) -> VideoGenerationResult:
        """Persist final costs and return the generation result."""
        image_cost = video.shots_cost(video.shots)
        total = AICost(
            token_count=tts_cost.token_count
            + seg_cost.token_count
            + image_cost.token_count,
            cost_usd=tts_cost.cost_usd + seg_cost.cost_usd + image_cost.cost_usd,
        )

        video.status = VideoStatus.finished
        video.current_stage = VideoStage.done
        video.tts_cost_usd = tts_cost.cost_usd
        video.tts_token_count = tts_cost.token_count
        video.segmentation_cost_usd = seg_cost.cost_usd
        video.segmentation_token_count = seg_cost.token_count
        video.image_generation_cost_usd = image_cost.cost_usd
        video.image_generation_token_count = image_cost.token_count
        video.total_cost_usd = total.cost_usd
        video.total_token_count = total.token_count
        await self._session.commit()
        await self._emit_progress(video)

        logger.info("Video %s: pipeline complete", video.id)
        return VideoGenerationResult(
            video_id=str(video.id),
            duration_ms=edit_result.duration_ms,
            num_shots=len(video.shots),
            total=total,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_prompt(self, video_input: VideoCreate) -> str:
        """Resolve the generation prompt from input or app settings."""
        if video_input.prompt:
            return video_input.prompt
        app_settings = await self._app_settings.get()
        return app_settings.master_prompt or ""

    async def _update_stage(self, video: Video, stage: VideoStage) -> None:
        """Transition video to a new pipeline stage, persist, and emit SSE."""
        video.current_stage = stage
        await self._session.commit()
        await self._emit_progress(video)

    async def _handle_failure(self, video: Video, error: Exception) -> None:
        """Mark video as failed, persist error, clean up S3 artifacts, and emit SSE."""
        logger.error(
            "Video %s: failed at %s — %s", video.id, video.current_stage.value, error
        )
        video.status = VideoStatus.failed
        video.error_message = f"Failed at {video.current_stage.value}: {error}"
        try:
            await self._session.commit()
        except Exception:
            logger.exception("Video %s: failed to persist error status", video.id)
        try:
            self._storage.delete_prefix(f"{video.s3_prefix}/")
        except Exception:
            logger.warning(
                "Video %s: failed to clean up S3 artifacts", video.id, exc_info=True
            )
        await self._emit_progress(video)

    async def _emit_progress(self, video: Video) -> None:
        """Emit a video progress SSE event. Failures are logged, never raised."""
        try:
            event = VideoProgressEvent(
                video_id=str(video.id),
                batch_id=str(video.batch_id) if video.batch_id else None,
                status=video.status.value,
                stage=video.current_stage.value,
            )
            video_channel = EventChannel.video.value.format(video_id=video.id)
            await self._events.emit(video_channel, event)
            if video.batch_id:
                batch_channel = EventChannel.batch.value.format(batch_id=video.batch_id)
                await self._events.emit(batch_channel, event)
        except Exception:
            logger.warning(
                "Video %s: failed to emit SSE event", video.id, exc_info=True
            )
