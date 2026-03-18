"""Tests for VideoService edge cases — no real DB or external APIs."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.videos.enums import VideoStage, VideoStatus
from api.videos.schemas import VideoCreate
from api.videos.service import VideoService

VIDEO_ID = uuid.uuid4()


def _make_video(**kwargs):
    """Create a Video model instance for testing."""
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


MOCK_TEMPLATE = MagicMock(
    template_context="", image_config=MagicMock()
)


def _make_video_crud(video):
    """Create a mock VideoCrud that copies input fields onto the video."""
    crud = AsyncMock()

    async def create_side_effect(video_input):
        for field, value in video_input.model_dump(exclude_unset=True).items():
            setattr(video, field, value)
        return video

    crud.create.side_effect = create_side_effect
    return crud


def _build_service(
    *,
    session=None,
    storage=None,
    events=None,
    app_settings=None,
    video_crud=None,
    tts=None,
    segmentation=None,
    image_gen=None,
):
    return VideoService(
        session=session or AsyncMock(),
        storage=storage or MagicMock(),
        events=events or AsyncMock(),
        app_settings=app_settings or AsyncMock(),
        video_crud=video_crud or AsyncMock(),
        tts=tts or MagicMock(),
        segmentation=segmentation or AsyncMock(),
        image_gen=image_gen or MagicMock(),
        editor=MagicMock(),
    )


class TestVideoCreationInitialState:
    @pytest.mark.asyncio
    async def test_failure_records_stage_in_error_message(self):
        """When TTS fails, the error message should include the current stage name."""
        video = _make_video()
        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("API timeout")

        service = _build_service(
            session=session, tts=tts, video_crud=_make_video_crud(video)
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert "tts" in video.error_message.lower()


class TestFailureMarksVideoFailed:
    @pytest.mark.asyncio
    async def test_tts_failure_sets_failed_status(self):
        video = _make_video()
        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.side_effect = ConnectionError("ElevenLabs down")

        service = _build_service(
            session=session, tts=tts, video_crud=_make_video_crud(video)
        )

        with pytest.raises(ConnectionError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert "tts" in video.error_message.lower()

    @pytest.mark.asyncio
    async def test_segmentation_failure_sets_failed_status(self):
        video = _make_video()
        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.return_value = MagicMock(
            audio_s3_key="k",
            audio_duration_ms=1000,
            word_timestamps=[],
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="test prompt")

        seg = AsyncMock()
        seg.segment_script.side_effect = RuntimeError("Claude API error")

        service = _build_service(
            session=session,
            tts=tts,
            app_settings=app_settings,
            segmentation=seg,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert "segmentation" in video.error_message.lower()


class TestPromptResolution:
    @pytest.mark.asyncio
    async def test_explicit_prompt_used_over_settings(self):
        """When VideoInput has a prompt, it should be used instead of master_prompt."""
        video = _make_video()
        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.return_value = MagicMock(
            audio_s3_key="k",
            audio_duration_ms=1000,
            word_timestamps=[],
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )

        seg = AsyncMock()
        seg.segment_script.side_effect = RuntimeError("stop")

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="default prompt")

        service = _build_service(
            session=session,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice", prompt="custom prompt"),
            )

        assert video.prompt == "custom prompt"
        app_settings.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_to_settings_when_no_prompt(self):
        video = _make_video()
        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.return_value = MagicMock(
            audio_s3_key="k",
            audio_duration_ms=1000,
            word_timestamps=[],
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )

        seg = AsyncMock()
        seg.segment_script.side_effect = RuntimeError("stop")

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="from settings")

        service = _build_service(
            session=session,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.prompt == "from settings"
        app_settings.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_master_prompt_defaults_to_empty_string(self):
        video = _make_video()
        session = AsyncMock()

        tts = MagicMock()
        tts.synthesize.return_value = MagicMock(
            audio_s3_key="k",
            audio_duration_ms=1000,
            word_timestamps=[],
            cost=MagicMock(cost_usd=0.01, token_count=0),
        )

        seg = AsyncMock()
        seg.segment_script.side_effect = RuntimeError("stop")

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt=None)

        service = _build_service(
            session=session,
            tts=tts,
            segmentation=seg,
            app_settings=app_settings,
            video_crud=_make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.prompt == ""
