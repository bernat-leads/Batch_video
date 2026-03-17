"""Video generation service — orchestrates the full pipeline."""

import asyncio
import logging

from sqlalchemy import delete
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
        """Create a video record and run the full pipeline."""
        video_input.prompt = await self._resolve_prompt(video_input)
        video = await self._video_crud.create(video_input)
        await self._emit_progress(video)

        try:
            return await self._run_pipeline(video, template)
        except Exception as error:
            await self._handle_failure(video, error)
            raise

    async def retry_video(
        self,
        video: Video,
        template: VideoTemplate,
    ) -> VideoGenerationResult:
        """Retry a failed video from the stage that failed."""
        logger.info("Video %s: retrying from stage %s", video.id, video.current_stage)

        video.status = VideoStatus.processing
        video.error_message = None
        await self._session.commit()
        await self._emit_progress(video)

        try:
            return await self._run_pipeline(video, template, from_stage=str(video.current_stage))
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
        from_stage: str = VideoStage.queued.value,
    ) -> VideoGenerationResult:
        """Run the pipeline from the given stage onwards.

        Fresh runs start from 'queued'. Retries start from the failed stage.
        Each stage checks what's already persisted and skips completed work.
        """
        stages = [stage.value for stage in VideoStage]
        start_index = stages.index(from_stage)

        # Stage 1: TTS
        if start_index <= stages.index(VideoStage.tts.value):
            tts_result = await self._run_tts(video)
        else:
            tts_result = await self._build_tts_result_from_storage(video)

        # Stage 2: Segmentation + create shots
        if start_index <= stages.index(VideoStage.segmentation.value):
            seg_result = await self._run_segmentation(video, tts_result, template)
            await self._delete_existing_shots(video)
            shots = await self._create_shots(video, seg_result)
        else:
            shots = list(video.shots)

        # Stage 3: Image generation (skips shots that already have images)
        if start_index <= stages.index(VideoStage.image_generation.value):
            await self._run_image_generation(video, shots, template)

        # Stage 4: Assembly
        await asyncio.to_thread(self._load_shot_images, shots)
        edit_result = await self._run_assembly(video, shots, tts_result, template)

        # Stage 5: Upload
        await self._run_upload(video, edit_result)

        return await self._finalize(video)

    async def _build_tts_result_from_storage(self, video: Video) -> TTSResult:
        """Rebuild TTSResult from S3 audio + shot timing for retry."""
        audio_bytes = await asyncio.to_thread(self._storage.download_file, video.audio_url)
        word_timestamps = video.build_word_timestamps()
        return TTSResult(
            audio_bytes=audio_bytes,
            content_type="audio/mpeg",
            audio_duration_ms=int(word_timestamps[-1].end * 1000) if word_timestamps else 0,
            word_timestamps=word_timestamps,
            cost=AICost(cost_usd=video.tts_cost_usd, token_count=video.tts_token_count),
        )

    async def _delete_existing_shots(self, video: Video) -> None:
        """Delete any existing shots for a video (for retry)."""
        await self._session.execute(delete(Shot).where(Shot.video_id == video.id))
        await self._session.flush()

    def _load_shot_images(self, shots: list[Shot]) -> None:
        """Download shot images from S3 for shots that don't have them in memory."""
        for shot in shots:
            if not getattr(shot, "image_bytes", None) and shot.image_url:
                shot.image_bytes = self._storage.download_file(shot.image_url)

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
        video.tts_cost_usd = tts_result.cost.cost_usd
        video.tts_token_count = tts_result.cost.token_count
        self._update_totals(video)
        await self._session.commit()
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
        video.segmentation_cost_usd = seg_result.cost.cost_usd
        video.segmentation_token_count = seg_result.cost.token_count
        self._update_totals(video)
        await self._session.commit()
        return seg_result

    async def _create_shots(self, video: Video, seg_result: SegmentationResult) -> list[Shot]:
        """Create shot records in DB from segmentation results (no images yet)."""
        shots: list[Shot] = []
        for segment in seg_result.segments:
            shot = Shot(
                video_id=video.id,
                order=segment.order,
                text=segment.text,
                image_prompt=segment.image_prompt,
                effect_config=segment.effect.model_dump(),
                start_time=segment.start_time,
                end_time=segment.end_time,
            )
            self._session.add(shot)
            shots.append(shot)
        await self._session.flush()
        return shots

    async def _run_image_generation(
        self, video: Video, shots: list[Shot], template: VideoTemplate
    ) -> None:
        """Stage 3: Generate images for each shot and upload to S3."""
        await self._update_stage(video, VideoStage.image_generation)

        for shot in shots:
            if shot.image_url:
                continue  # already generated (partial retry)
            await asyncio.to_thread(
                self._generate_shot_image, video, shot, template.image_config
            )

        image_cost = video.shots_cost(shots)
        video.image_generation_cost_usd = image_cost.cost_usd
        video.image_generation_token_count = image_cost.token_count
        self._update_totals(video)
        await self._session.commit()

    def _generate_shot_image(self, video: Video, shot: Shot, image_config: ImageConfig) -> None:
        """Generate image for a shot and upload to S3 (runs in thread)."""
        image_result = self._image_gen.generate_image(shot.image_prompt, image_config)

        s3_key = video.shot_s3_key(shot.order)
        self._storage.upload_file(s3_key, image_result.image_bytes, image_result.content_type)

        shot.image_url = s3_key
        shot.cost_usd = image_result.cost.cost_usd
        shot.image_bytes = image_result.image_bytes  # transient — used by assembly

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

    async def _finalize(self, video: Video) -> VideoGenerationResult:
        """Mark finished and return the generation result."""
        video.status = VideoStatus.finished
        video.current_stage = VideoStage.done
        await self._session.commit()
        await self._emit_progress(video)

        logger.info("Video %s: pipeline complete", video.id)
        return VideoGenerationResult(
            video_id=str(video.id),
            duration_ms=video.duration_ms,
            num_shots=len(video.shots),
            total=video.total,
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

    @staticmethod
    def _update_totals(video: Video) -> None:
        """Recompute total cost and token count from per-stage values."""
        video.total_cost_usd = (
            video.tts_cost_usd + video.segmentation_cost_usd + video.image_generation_cost_usd
        )
        video.total_token_count = (
            video.tts_token_count + video.segmentation_token_count + video.image_generation_token_count
        )

    async def _update_stage(self, video: Video, stage: VideoStage) -> None:
        """Transition video to a new pipeline stage, persist, and emit SSE."""
        video.current_stage = stage
        await self._session.commit()
        await self._emit_progress(video)

    async def _handle_failure(self, video: Video, error: Exception) -> None:
        """Mark video as failed, persist error, and emit SSE.

        S3 artifacts are NOT cleaned up — they may be needed for retry.
        The retention cleanup task handles orphaned artifacts.
        """
        logger.error(
            "Video %s: failed at %s — %s", video.id, video.current_stage, error
        )
        video.status = VideoStatus.failed
        video.error_message = f"Failed at {video.current_stage}: {error}"
        try:
            await self._session.commit()
        except Exception:
            logger.exception("Video %s: failed to persist error status", video.id)
        await self._emit_progress(video)

    async def _emit_progress(self, video: Video) -> None:
        """Emit a video progress SSE event. Failures are logged, never raised."""
        try:
            event = VideoProgressEvent(
                video_id=str(video.id),
                batch_id=str(video.batch_id) if video.batch_id else None,
                status=video.status,
                stage=video.current_stage,
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
