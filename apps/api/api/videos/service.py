"""Video generation service — orchestrates the full pipeline."""

import asyncio
import logging
import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import SegmentationEmptyError
from api.core.schemas import AICost
from api.events.schemas import EventChannel
from api.events.service import EventService
from api.settings_module.crud import AppSettingsCrud
from api.shots.models.shot import Shot
from api.shots.service import ShotService
from api.storage import StorageService
from api.videos.enums import VideoStage, VideoStatus
from api.videos.models.video import Video
from api.videos.pipeline.segmentation import SegmentationService
from api.videos.pipeline.tts import TTSService
from api.videos.pipeline.video_editor import CaptionWord, Segment, VideoTemplate
from api.videos.schemas import VideoCreate, VideoGenerationResult, VideoProgressEvent

logger = logging.getLogger(__name__)


class VideoService:
    """Orchestrates the full video generation pipeline.

    Receives all dependencies via constructor. The caller (Celery task)
    is responsible for constructing this service with the right deps.
    """

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        events: EventService,
        app_settings: AppSettingsCrud,
        tts: TTSService,
        segmentation: SegmentationService,
        shots: ShotService,
        video_template: VideoTemplate,
    ) -> None:
        """Initialize with all pipeline dependencies."""
        self._session = session
        self._storage = storage
        self._events = events
        self._app_settings = app_settings
        self._tts = tts
        self._segmentation = segmentation
        self._shots = shots
        self._video_template = video_template

    async def generate_video(
        self,
        video_id: uuid.UUID,
        video_input: VideoCreate,
    ) -> VideoGenerationResult:
        """Run the full pipeline for an existing video record.

        Resets the video to a clean state (deletes old shots, clears errors),
        then executes all stages sequentially. On failure, marks the video as
        failed and cleans up partial R2 artifacts.
        """
        video = await self._reset_video(video_id)

        try:
            return await self._run_pipeline(video, video_input)
        except Exception as error:
            await self._handle_failure(video, error)
            raise

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    async def _run_pipeline(
        self, video: Video, video_input: VideoCreate
    ) -> VideoGenerationResult:
        """Execute all pipeline stages and persist the final result."""
        tts_result = await self._run_tts(video, video_input)
        seg_result = await self._run_segmentation(video, video_input, tts_result)
        num_shots, image_cost = await self._run_image_generation(video, seg_result)
        edit_result = await self._run_assembly(
            video, seg_result, tts_result, video_input
        )
        output_key = await self._run_upload(video, edit_result)

        return await self._finalize(
            video,
            output_key,
            edit_result,
            num_shots,
            tts_result.cost,
            seg_result.cost,
            image_cost,
        )

    async def _run_tts(self, video, video_input):
        """Stage 1: Convert script to speech with word-level timestamps."""
        await self._update_stage(video, VideoStage.tts)
        return await asyncio.to_thread(
            self._tts.synthesize,
            video_input.script_text,
            video_input.voice_id,
            video.id,
        )

    async def _run_segmentation(self, video, video_input, tts_result):
        """Stage 2: Segment script into visual chunks with image prompts."""
        await self._update_stage(video, VideoStage.segmentation)
        prompt = await self._resolve_prompt(video_input)
        video.prompt = prompt
        seg_result = await self._segmentation.segment_script(
            video_input.script_text,
            tts_result.word_timestamps,
            video_input.style,
            prompt=prompt,
        )
        if not seg_result.segments:
            raise SegmentationEmptyError()
        return seg_result

    async def _run_image_generation(self, video, seg_result) -> tuple[int, AICost]:
        """Stage 3: Generate images for all segments. Returns (count, cost).

        Image generation (network I/O) runs in parallel via asyncio.gather,
        but shot DB writes run sequentially — AsyncSession is not safe for
        concurrent coroutine access.
        """
        await self._update_stage(video, VideoStage.image_generation)

        # Parallelize the expensive image generation calls (no DB access)
        image_tasks = [
            asyncio.to_thread(self._shots.image_gen.generate_image, segment)
            for segment in seg_result.segments
        ]
        image_results = await asyncio.gather(*image_tasks)

        # Persist shots sequentially — session is not concurrency-safe
        shots: list[Shot] = []
        for segment, image_result in zip(seg_result.segments, image_results):
            shot = await self._shots.create_shot_with_image(
                video.id, segment, image_result
            )
            shots.append(shot)

        return len(shots), AICost(cost_usd=sum(s.cost_usd for s in shots))

    async def _run_assembly(self, video, seg_result, tts_result, video_input):
        """Stage 4: Compose final video from images, audio, and captions.

        Downloads images from R2, then runs the CPU-bound MoviePy render
        in a thread to avoid blocking the event loop.
        """
        await self._update_stage(video, VideoStage.assembly)

        # Download images and audio from R2 (sync I/O, run in thread)
        segments = await asyncio.to_thread(
            self._download_segments, video.id, seg_result.segments
        )
        audio_bytes = await asyncio.to_thread(
            self._storage.download_file, tts_result.audio_r2_key
        )

        captions = [
            CaptionWord(word=word.word, start=word.start, end=word.end)
            for word in tts_result.word_timestamps
        ]

        # CPU-bound render — must not block the event loop
        return await asyncio.to_thread(
            self._video_template.assemble_video,
            segments,
            audio_bytes,
            captions,
            video_input.top_text,
        )

    def _download_segments(self, video_id: uuid.UUID, segments) -> list[Segment]:
        """Download shot images from R2 and build Segment objects."""
        return [
            Segment(
                image_bytes=self._storage.download_file(
                    f"videos/{video_id}/shots/{seg.order:03d}.png"
                ),
                duration=seg.end_time - seg.start_time,
                ken_burns=seg.ken_burns_config,
            )
            for seg in segments
        ]

    async def _run_upload(self, video, edit_result):
        """Stage 5: Upload the rendered video to R2."""
        await self._update_stage(video, VideoStage.upload)
        output_key = f"videos/{video.id}/output.mp4"
        await asyncio.to_thread(
            self._storage.upload_file, output_key, edit_result.video_bytes, "video/mp4"
        )
        return output_key

    async def _finalize(
        self, video, output_key, edit_result, num_shots, tts_cost, seg_cost, image_cost
    ):
        """Persist final video state and return the generation result."""
        total = AICost(
            token_count=tts_cost.token_count
            + seg_cost.token_count
            + image_cost.token_count,
            cost_usd=tts_cost.cost_usd + seg_cost.cost_usd + image_cost.cost_usd,
        )

        video.status = VideoStatus.finished
        video.current_stage = VideoStage.done
        video.output_url = output_key
        video.duration_ms = edit_result.duration_ms
        video.file_size_bytes = len(edit_result.video_bytes)
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
            video_r2_key=output_key,
            file_size_bytes=len(edit_result.video_bytes),
            duration_ms=edit_result.duration_ms,
            num_shots=num_shots,
            tts=tts_cost,
            segmentation=seg_cost,
            image_generation=image_cost,
            total=total,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _reset_video(self, video_id: uuid.UUID) -> Video:
        """Load a video, reset its state, and delete any previous shots."""
        video = await self._session.get(Video, video_id)
        video.status = VideoStatus.processing
        video.current_stage = VideoStage.queued
        video.error_message = None
        await self._session.execute(sa_delete(Shot).where(Shot.video_id == video.id))
        await self._session.commit()
        await self._emit_progress(video)
        return video

    async def _resolve_prompt(self, video_input: VideoCreate) -> str:
        """Resolve the generation prompt: explicit input takes priority over app settings."""
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
        """Mark video as failed, persist error, clean up R2 artifacts, and emit SSE."""
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
            self._storage.delete_prefix(f"videos/{video.id}/")
        except Exception:
            logger.warning(
                "Video %s: failed to clean up R2 artifacts", video.id, exc_info=True
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
