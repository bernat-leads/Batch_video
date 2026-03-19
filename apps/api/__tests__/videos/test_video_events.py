"""Tests for SSE event emission timing during the video pipeline.

Verifies that _emit_progress is called at the right moments:
- After video creation (queued)
- On each stage transition (tts, segmentation, image_generation, assembly, upload)
- On each shot status change (generating, generated)
- On finalize (done)
- On failure
"""

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from api.shots.enums import ShotStatus
from api.videos.enums import VideoStage, VideoStatus
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


def _count_emits(events: AsyncMock) -> int:
    """Count how many times events.emit was called."""
    return events.emit.call_count


class TestStageTransitionEvents:
    """Each stage transition should emit an SSE event."""

    async def test_tts_failure_emits_creation_plus_stage_plus_failure(self):
        """queued emit + tts stage emit + failure emit = 3 emits."""
        video = make_video()
        events = AsyncMock()
        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("TTS broke")

        service = build_service(
            session=AsyncMock(),
            events=events,
            tts=tts,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        # 1: after create (queued), 2: stage→tts, 3: failure
        assert _count_emits(events) == 3

    async def test_segmentation_failure_emits_correct_count(self):
        """queued + tts stage + segmentation stage + failure = 4 emits."""
        video = make_video()
        events = AsyncMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_tts_result()
        seg = AsyncMock()
        seg.segment_script.side_effect = RuntimeError("Seg broke")

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")

        service = build_service(
            session=AsyncMock(),
            events=events,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        # 1: queued, 2: tts stage, 3: segmentation stage, 4: failure
        assert _count_emits(events) == 4


class TestShotGenerationEvents:
    """Shot status changes should emit SSE events."""

    async def test_single_shot_emits_generating_and_generated(self):
        """Each shot should emit on generating + generated status changes."""
        video = make_video()
        events = AsyncMock()
        session = AsyncMock()
        session.add = MagicMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_real_tts_result()
        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(
            segments=[make_mock_segment()]
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

        service = build_service(
            session=session,
            events=events,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            image_gen=image_gen,
            editor=editor,
            video_crud=make_video_crud(video),
        )

        await service.generate_video(
            template=REAL_TEMPLATE,
            video_input=VideoCreate(script_text="hello", voice_id="v1"),
        )

        # Expected emits for 1 shot:
        # 1: queued (create)
        # 2: tts stage
        # 3: segmentation stage
        # 4: image_generation stage
        # 5: shot generating
        # 6: shot generated
        # 7: assembly stage
        # 8: upload stage
        # 9: finalize (done)
        assert _count_emits(events) == 9

    async def test_multiple_shots_emit_per_shot(self):
        """N shots should emit 2*N events during image generation."""
        video = make_video()
        events = AsyncMock()
        session = AsyncMock()
        session.add = MagicMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_real_tts_result()

        seg1 = make_mock_segment()
        seg1.order = 0
        seg2 = make_mock_segment()
        seg2.order = 1
        seg3 = make_mock_segment()
        seg3.order = 2

        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(
            segments=[seg1, seg2, seg3]
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

        service = build_service(
            session=session,
            events=events,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            image_gen=image_gen,
            editor=editor,
            video_crud=make_video_crud(video),
        )

        await service.generate_video(
            template=REAL_TEMPLATE,
            video_input=VideoCreate(script_text="hello", voice_id="v1"),
        )

        # 1: queued
        # 2: tts stage
        # 3: segmentation stage
        # 4: image_generation stage
        # 5-10: 3 shots × (generating + generated) = 6
        # 11: assembly stage
        # 12: upload stage
        # 13: finalize
        assert _count_emits(events) == 13

    async def test_shot_failure_emits_event(self):
        """A shot failing should emit on generating + failed status."""
        video = make_video()
        events = AsyncMock()
        session = AsyncMock()
        session.add = MagicMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_tts_result()
        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(
            segments=[make_mock_segment()]
        )
        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="prompt")
        image_gen = MagicMock()
        image_gen.generate_image.side_effect = RuntimeError("Gemini down")

        service = build_service(
            session=session,
            events=events,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            image_gen=image_gen,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError, match="Gemini down"):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        # 1: queued
        # 2: tts stage
        # 3: segmentation stage
        # 4: image_generation stage
        # 5: shot generating
        # 6: shot failed
        # 7: video failure
        assert _count_emits(events) == 7


class TestFinalizeEvent:
    """Finalize should emit a done event."""

    async def test_successful_pipeline_emits_done(self):
        video = make_video()
        events = AsyncMock()
        session = AsyncMock()
        session.add = MagicMock()
        tts = MagicMock()
        tts.synthesize.return_value = make_real_tts_result()
        seg = AsyncMock()
        seg.segment_script.return_value = make_seg_result(
            segments=[make_mock_segment()]
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

        service = build_service(
            session=session,
            events=events,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            image_gen=image_gen,
            editor=editor,
            video_crud=make_video_crud(video),
        )

        await service.generate_video(
            template=REAL_TEMPLATE,
            video_input=VideoCreate(script_text="hello", voice_id="v1"),
        )

        assert video.status == VideoStatus.finished
        assert video.current_stage == VideoStage.done
        # 9 emits total for 1-shot successful pipeline
        assert events.emit.call_count == 9


class TestBatchChannelEmission:
    """When video has a batch_id, events should emit to both channels."""

    async def test_batch_video_emits_to_both_channels(self):
        import uuid

        batch_id = uuid.uuid4()
        video = make_video(batch_id=batch_id)
        events = AsyncMock()
        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("stop")

        service = build_service(
            session=AsyncMock(),
            events=events,
            tts=tts,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        # Each _emit_progress call emits to video channel + batch channel = 2 calls
        # 3 logical emits (queued, tts stage, failure) × 2 channels = 6
        assert events.emit.call_count == 6

    async def test_non_batch_video_emits_to_video_channel_only(self):
        video = make_video(batch_id=None)
        events = AsyncMock()
        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("stop")

        service = build_service(
            session=AsyncMock(),
            events=events,
            tts=tts,
            video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        # 3 logical emits × 1 channel = 3
        assert events.emit.call_count == 3
