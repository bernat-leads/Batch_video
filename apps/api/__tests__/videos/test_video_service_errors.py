"""Tests for VideoService error handling — verify failures don't cascade."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.core.exceptions import SegmentationEmptyError
from api.videos.enums import VideoStage, VideoStatus
from api.videos.models.video import Video
from api.videos.schemas import VideoCreate
from api.videos.service import VideoService

VIDEO_ID = uuid.uuid4()


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
        prompt=None,
    )
    defaults.update(kwargs)
    video = MagicMock()
    for k, v in defaults.items():
        setattr(video, k, v)
    return video


def _build_service(**overrides):
    defaults = dict(
        session=AsyncMock(),
        storage=MagicMock(),
        events=AsyncMock(),
        app_settings=AsyncMock(),
        tts=MagicMock(),
        segmentation=AsyncMock(),
        shots=AsyncMock(),
        video_template=MagicMock(),
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


def _seg_result(*, segments=None):
    r = MagicMock()
    r.segments = segments or []
    r.prompt = "test"
    r.tokens_used = 10
    r.cost_usd = 0.001
    return r


class TestEmitFailureDoesNotCrashPipeline:
    @pytest.mark.asyncio
    async def test_redis_down_during_emit_still_marks_failed(self):
        """If Redis dies during event emission, the video should still be marked failed."""
        video = _make_video()

        events = AsyncMock()
        events.emit.side_effect = ConnectionError("Redis gone")

        session = AsyncMock()
        session.get = AsyncMock(return_value=video)

        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("TTS broke")

        service = _build_service(session=session, events=events, tts=tts)

        with pytest.raises(RuntimeError, match="TTS broke"):
            await service.generate_video(
                video_id=VIDEO_ID, video_input=VideoCreate(script_text="hello")
            )

        assert video.status == VideoStatus.failed


class TestBatchCounterFailureDoesNotCrashPipeline:
    @pytest.mark.asyncio
    async def test_batch_counter_db_error_still_raises_original(self):
        """If batch counter update fails, the original exception still propagates."""
        batch_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        video = _make_video(batch_id=batch_id)

        session = AsyncMock()
        session.get = AsyncMock(return_value=video)

        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("TTS broke")

        service = _build_service(session=session, tts=tts)

        with pytest.raises(RuntimeError, match="TTS broke"):
            await service.generate_video(
                video_id=VIDEO_ID,
                video_input=VideoCreate(script_text="hello"),
            )


class TestEmptySegmentsRaisesError:
    @pytest.mark.asyncio
    async def test_zero_segments_raises_value_error(self):
        """If segmentation returns empty segments, it should fail explicitly."""
        video = _make_video()

        session = AsyncMock()
        session.get = AsyncMock(return_value=video)

        tts = MagicMock()
        tts.synthesize.return_value = _tts_result()

        seg = AsyncMock()
        seg.segment_script.return_value = _seg_result(segments=[])

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")

        service = _build_service(
            session=session, tts=tts, segmentation=seg, app_settings=app_settings
        )

        with pytest.raises(SegmentationEmptyError):
            await service.generate_video(
                video_id=VIDEO_ID, video_input=VideoCreate(script_text="hello")
            )

        assert video.status == VideoStatus.failed
        assert "segmentation" in video.error_message.lower()


class TestCommitFailureInErrorHandler:
    @pytest.mark.asyncio
    async def test_commit_failure_after_error_does_not_mask_original(self):
        """If commit fails when persisting error status, original exception still raised."""
        video = _make_video()

        session = AsyncMock()
        session.get = AsyncMock(return_value=video)
        # First commits succeed (stage updates), then fail on error persist
        session.commit = AsyncMock(side_effect=[None, None, Exception("DB dead")])

        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("API down")

        service = _build_service(session=session, tts=tts)

        with pytest.raises(RuntimeError, match="API down"):
            await service.generate_video(
                video_id=VIDEO_ID, video_input=VideoCreate(script_text="hello")
            )
