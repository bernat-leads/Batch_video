"""Tests for VideoService error handling — verify failures don't cascade."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.core.exceptions import SegmentationEmptyError
from api.core.schemas import AICost
from api.videos.enums import VideoStage, VideoStatus
from api.videos.pipeline.tts.schemas import TTSResult
from api.videos.pipeline.video_editor.schemas import VideoTemplate
from api.videos.schemas import VideoCreate
from api.videos.service import VideoService

VIDEO_ID = uuid.uuid4()
MOCK_TEMPLATE = MagicMock(
    template_context="", image_config=MagicMock()
)
REAL_TEMPLATE = VideoTemplate()


def _make_video(**kwargs):
    defaults = dict(
        id=VIDEO_ID,
        script_text="hello",
        status=VideoStatus.processing,
        current_stage=VideoStage.queued,
        batch_id=None,
        error_message=None,
        output_url=None,
        tts_cost_usd=0.0,
        tts_token_count=0,
        segmentation_cost_usd=0.0,
        segmentation_token_count=0,
        image_generation_cost_usd=0.0,
        image_generation_token_count=0,
        total_cost_usd=0.0,
        total_token_count=0,
        file_size_bytes=0,
        voice_id=None,
        style=None,
        top_text=None,
        prompt="",
    )
    defaults.update(kwargs)
    video = MagicMock()
    for key, value in defaults.items():
        setattr(video, key, value)
    return video


def _make_video_crud(video):
    """Create a mock VideoCrud that copies input fields onto the video."""
    crud = AsyncMock()

    async def create_side_effect(video_input):
        for field, value in video_input.model_dump(exclude_unset=True).items():
            setattr(video, field, value)
        return video

    crud.create.side_effect = create_side_effect
    return crud


def _build_service(**overrides):
    defaults = dict(
        session=AsyncMock(),
        storage=MagicMock(),
        events=AsyncMock(),
        app_settings=AsyncMock(),
        video_crud=AsyncMock(),
        tts=MagicMock(),
        segmentation=AsyncMock(),
        image_gen=MagicMock(),
        editor=MagicMock(),
    )
    defaults.update(overrides)
    return VideoService(**defaults)


def _tts_result():
    return MagicMock(
        audio_s3_key="k",
        audio_duration_ms=1000,
        word_timestamps=[],
        cost=MagicMock(cost_usd=0.01, token_count=0),
    )


def _real_tts_result():
    """Create a real TTSResult with actual bytes for tests that reach assembly."""
    return TTSResult(
        audio_bytes=b"fake-audio-data",
        content_type="audio/mpeg",
        audio_duration_ms=1000,
        word_timestamps=[],
        cost=AICost(cost_usd=0.01, token_count=0),
    )


def _seg_result(*, segments=None):
    result = MagicMock()
    result.segments = segments or []
    result.prompt = "test"
    result.tokens_used = 10
    result.cost_usd = 0.001
    return result


class TestEmitFailureDoesNotCrashPipeline:
    @pytest.mark.asyncio
    async def test_redis_down_during_emit_still_marks_failed(self):
        """If Redis dies during event emission, the video should still be marked failed."""
        video = _make_video()

        events = AsyncMock()
        events.emit.side_effect = ConnectionError("Redis gone")

        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("TTS broke")

        service = _build_service(
            session=session, events=events, tts=tts,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="TTS broke"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed


class TestBatchCounterFailureDoesNotCrashPipeline:
    @pytest.mark.asyncio
    async def test_batch_counter_db_error_still_raises_original(self):
        """If batch counter update fails, the original exception still propagates."""
        batch_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        video = _make_video(batch_id=batch_id)

        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("TTS broke")

        service = _build_service(
            session=session, tts=tts,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="TTS broke"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )


class TestEmptySegmentsRaisesError:
    @pytest.mark.asyncio
    async def test_zero_segments_raises_value_error(self):
        """If segmentation returns empty segments, it should fail explicitly."""
        video = _make_video()

        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.return_value = _tts_result()

        seg = AsyncMock()
        seg.segment_script.return_value = _seg_result(segments=[])

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")

        service = _build_service(
            session=session, tts=tts, segmentation=seg, app_settings=app_settings,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(SegmentationEmptyError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert "segmentation" in video.error_message.lower()


class TestCommitFailureInErrorHandler:
    @pytest.mark.asyncio
    async def test_commit_failure_after_error_does_not_mask_original(self):
        """If commit fails when persisting error status, original exception still raised."""
        video = _make_video()

        session = AsyncMock()
        # Commits: (1) update_stage(tts) succeeds;
        # Then TTS fails with RuntimeError; (2) _handle_failure commit fails
        session.commit = AsyncMock(
            side_effect=[None, Exception("DB dead")]
        )

        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("API down")

        service = _build_service(
            session=session, tts=tts,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="API down"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )


class TestImageGenerationFailure:
    @pytest.mark.asyncio
    async def test_image_gen_failure_sets_failed_status(self):
        """If image generation fails, video should be marked failed at image_generation stage."""
        video = _make_video()
        session = AsyncMock()
        session.add = MagicMock()

        tts = MagicMock()
        tts.synthesize.return_value = _tts_result()

        seg = AsyncMock()
        mock_segment = MagicMock()
        mock_segment.order = 0
        mock_segment.image_prompt = "test"
        mock_segment.effect = MagicMock()
        mock_segment.effect.model_dump.return_value = {
            "type": "ken_burns", "direction": "zoom_in", "scale": 1.2,
        }
        seg.segment_script.return_value = _seg_result(segments=[mock_segment])

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")

        image_gen = MagicMock()
        image_gen.generate_image.side_effect = RuntimeError("Gemini API error")

        service = _build_service(
            session=session,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            image_gen=image_gen,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="Gemini API error"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert "image_generation" in video.error_message.lower()


def _make_mock_segment():
    """Create a realistic mock segment that passes through _generate_shot."""
    mock_segment = MagicMock()
    mock_segment.order = 0
    mock_segment.image_prompt = "A vivid scene"
    mock_segment.text = "hello world"
    mock_segment.start_time = 0.0
    mock_segment.end_time = 5.0
    mock_segment.effect = MagicMock()
    mock_segment.effect.model_dump.return_value = {
        "type": "ken_burns", "direction": "zoom_in", "scale": 1.2,
    }
    return mock_segment


class TestAssemblyFailure:
    @pytest.mark.asyncio
    async def test_assembly_failure_sets_failed_status(self):
        """If video assembly fails, video should be marked failed at assembly stage."""
        video = _make_video()
        session = AsyncMock()
        session.add = MagicMock()

        tts = MagicMock()
        tts.synthesize.return_value = _real_tts_result()

        seg = AsyncMock()
        seg.segment_script.return_value = _seg_result(
            segments=[_make_mock_segment()]
        )

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")

        image_gen = MagicMock()
        image_gen.generate_image.return_value = MagicMock(
            image_bytes=b"png",
            content_type="image/png",
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )

        editor = MagicMock()
        editor.assemble_video.side_effect = RuntimeError("FFmpeg crashed")

        service = _build_service(
            session=session,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            image_gen=image_gen,
            editor=editor,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="FFmpeg crashed"):
            await service.generate_video(
                template=REAL_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert "assembly" in video.error_message.lower()


class TestUploadFailure:
    @pytest.mark.asyncio
    async def test_upload_failure_sets_failed_status(self):
        """If S3 upload fails during upload stage, video should be marked failed."""
        video = _make_video()
        session = AsyncMock()
        session.add = MagicMock()

        tts = MagicMock()
        tts.synthesize.return_value = _real_tts_result()

        seg = AsyncMock()
        seg.segment_script.return_value = _seg_result(
            segments=[_make_mock_segment()]
        )

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")

        image_gen = MagicMock()
        image_gen.generate_image.return_value = MagicMock(
            image_bytes=b"png",
            content_type="image/png",
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )

        editor = MagicMock()
        editor.assemble_video.return_value = MagicMock(
            video_bytes=b"mp4", duration_ms=5000
        )

        storage = MagicMock()

        def _upload_side_effect(key, data, content_type):
            if content_type == "video/mp4":
                raise RuntimeError("S3 upload failed")

        storage.upload_file.side_effect = _upload_side_effect

        service = _build_service(
            session=session,
            storage=storage,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            image_gen=image_gen,
            editor=editor,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="S3 upload failed"):
            await service.generate_video(
                template=REAL_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert "upload" in video.error_message.lower()
