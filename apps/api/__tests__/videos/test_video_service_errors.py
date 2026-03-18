"""Tests for VideoService error handling — verify failures don't cascade."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.core.exceptions import SegmentationEmptyError
from api.videos.enums import VideoStatus
from api.videos.pipeline.video_editor.schemas import VideoTemplate
from api.videos.schemas import VideoCreate
from __tests__.helpers import (
    MOCK_TEMPLATE,
    build_service,
    make_mock_segment,
    make_real_tts_result,
    make_seg_result,
    make_tts_result,
    make_video,
    make_video_crud,
)

REAL_TEMPLATE = VideoTemplate()


class TestEmitFailureDoesNotCrashPipeline:
    async def test_redis_down_during_emit_still_marks_failed(self):
        video = make_video()
        events = AsyncMock()
        events.emit.side_effect = ConnectionError("Redis gone")
        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("TTS broke")

        service = build_service(
            session=AsyncMock(), events=events, tts=tts,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="TTS broke"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        assert video.status == VideoStatus.failed


class TestEmptySegmentsRaisesError:
    async def test_zero_segments_raises_error(self):
        video = make_video()
        tts = MagicMock()
        tts.synthesize.return_value = make_tts_result()
        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(segments=[])
        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")

        service = build_service(
            session=AsyncMock(), tts=tts, segmentation=seg,
            app_settings=app_settings, video_crud=make_video_crud(video),
        )

        with pytest.raises(SegmentationEmptyError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        assert video.status == VideoStatus.failed
        assert "segmentation" in video.error_message.lower()


class TestCommitFailureInErrorHandler:
    async def test_commit_failure_does_not_mask_original(self):
        video = make_video()
        session = AsyncMock()
        session.commit = AsyncMock(side_effect=[None, Exception("DB dead")])
        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("API down")

        service = build_service(
            session=session, tts=tts, video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="API down"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )


class TestPipelineStageFailures:
    """Each pipeline stage failure should mark the video failed with the correct stage."""

    async def test_image_gen_failure(self):
        video = make_video()
        session = AsyncMock()
        session.add = MagicMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_tts_result()
        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(segments=[make_mock_segment()])
        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")
        image_gen = MagicMock()
        image_gen.generate_image.side_effect = RuntimeError("Gemini API error")

        service = build_service(
            session=session, tts=tts, segmentation=seg,
            app_settings=app_settings, image_gen=image_gen,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="Gemini API error"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        assert video.status == VideoStatus.failed
        assert "image_generation" in video.error_message.lower()

    async def test_assembly_failure(self):
        video = make_video()
        session = AsyncMock()
        session.add = MagicMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_real_tts_result()
        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(segments=[make_mock_segment()])
        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")
        image_gen = MagicMock()
        image_gen.generate_image.return_value = MagicMock(
            image_bytes=b"png", content_type="image/png",
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )
        editor = MagicMock()
        editor.assemble_video.side_effect = RuntimeError("FFmpeg crashed")

        service = build_service(
            session=session, tts=tts, segmentation=seg,
            app_settings=app_settings, image_gen=image_gen, editor=editor,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="FFmpeg crashed"):
            await service.generate_video(
                template=REAL_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        assert video.status == VideoStatus.failed
        assert "assembly" in video.error_message.lower()

    async def test_upload_failure(self):
        video = make_video()
        session = AsyncMock()
        session.add = MagicMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_real_tts_result()
        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(segments=[make_mock_segment()])
        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")
        image_gen = MagicMock()
        image_gen.generate_image.return_value = MagicMock(
            image_bytes=b"png", content_type="image/png",
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )
        editor = MagicMock()
        editor.assemble_video.return_value = MagicMock(video_bytes=b"mp4", duration_ms=5000)
        storage = MagicMock()

        def _upload_side_effect(key, data, content_type):
            if content_type == "video/mp4":
                raise RuntimeError("S3 upload failed")

        storage.upload_file.side_effect = _upload_side_effect

        service = build_service(
            session=session, storage=storage, tts=tts, segmentation=seg,
            app_settings=app_settings, image_gen=image_gen, editor=editor,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="S3 upload failed"):
            await service.generate_video(
                template=REAL_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        assert video.status == VideoStatus.failed
        assert "upload" in video.error_message.lower()
