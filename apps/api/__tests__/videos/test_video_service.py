"""Tests for VideoService edge cases — no real DB or external APIs."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from api.videos.enums import VideoStatus
from api.videos.schemas import VideoCreate
from __tests__.helpers import (
    MOCK_TEMPLATE,
    build_service,
    make_tts_result,
    make_video,
    make_video_crud,
)


class TestStageFailureMarksVideoFailed:
    """When a pipeline stage fails, the video should be marked failed with the stage name."""

    @pytest.mark.parametrize(
        "failing_stage, stage_overrides",
        [
            pytest.param("tts", dict(tts=MagicMock()), id="tts-failure"),
            pytest.param("segmentation", dict(segmentation=AsyncMock()), id="segmentation-failure"),
        ],
    )
    async def test_failure_sets_failed_status_and_records_stage(self, failing_stage, stage_overrides):
        video = make_video()
        session = AsyncMock()

        # Configure the failing stage
        for key, mock in stage_overrides.items():
            if key == "tts":
                mock.synthesize.side_effect = RuntimeError(f"{failing_stage} broke")
            elif key == "segmentation":
                mock.segment_script.side_effect = RuntimeError(f"{failing_stage} broke")

        # If segmentation fails, TTS must succeed first
        if failing_stage != "tts":
            stage_overrides.setdefault("tts", MagicMock())
            stage_overrides["tts"].synthesize.return_value = make_tts_result()

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="test prompt")

        service = build_service(
            session=session,
            app_settings=app_settings,
            video_crud=make_video_crud(video),
            **stage_overrides,
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="test-voice"),
            )

        assert video.status == VideoStatus.failed
        assert failing_stage in video.error_message.lower()


class TestPromptResolution:
    async def test_explicit_prompt_used_over_settings(self):
        video = make_video()
        tts = MagicMock()
        tts.synthesize.return_value = make_tts_result()
        seg = AsyncMock()
        seg.segment_script.side_effect = RuntimeError("stop")

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt="default prompt")

        service = build_service(
            session=AsyncMock(), tts=tts, segmentation=seg,
            app_settings=app_settings, video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1", prompt="custom prompt"),
            )

        assert video.prompt == "custom prompt"
        app_settings.get.assert_not_called()

    @pytest.mark.parametrize(
        "master_prompt, expected",
        [
            pytest.param("from settings", "from settings", id="uses-settings"),
            pytest.param(None, "", id="none-defaults-to-empty"),
        ],
    )
    async def test_falls_back_to_settings(self, master_prompt, expected):
        video = make_video()
        tts = MagicMock()
        tts.synthesize.return_value = make_tts_result()
        seg = AsyncMock()
        seg.segment_script.side_effect = RuntimeError("stop")

        app_settings = AsyncMock()
        app_settings.get.return_value = MagicMock(master_prompt=master_prompt)

        service = build_service(
            session=AsyncMock(), tts=tts, segmentation=seg,
            app_settings=app_settings, video_crud=make_video_crud(video),
        )

        with pytest.raises(RuntimeError):
            await service.generate_video(
                template=MOCK_TEMPLATE,
                video_input=VideoCreate(script_text="hello", voice_id="v1"),
            )

        assert video.prompt == expected
