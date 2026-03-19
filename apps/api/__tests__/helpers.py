"""Test helpers — shared mock utilities."""

import uuid
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from api.core.schemas import AICost
from api.events.service import EventService
from api.settings_module.crud import AppSettingsCrud
from api.storage import StorageService
from api.videos.crud import VideoCrud
from api.videos.enums import VideoStage, VideoStatus
from api.videos.pipeline.image_generation.base import ImageGenService
from api.videos.pipeline.providers import PipelineProviders
from api.videos.pipeline.segmentation.base import SegmentationService
from api.videos.pipeline.tts.base import TTSService
from api.videos.pipeline.tts.schemas import TTSResult
from api.videos.pipeline.video_editor.base import VideoEditor
from api.videos.service import VideoService

VIDEO_ID = uuid.uuid4()

MOCK_TEMPLATE = MagicMock(template_context="", image_config=MagicMock())


def fake_db_obj(**kwargs):
    """Create a fake database object with the given attributes."""
    obj = MagicMock()
    for key, value in kwargs.items():
        setattr(obj, key, value)
    return obj


def mock_scalars_result(items: list, *, session: AsyncMock):
    """Mock session.execute() to return scalars().all() with the given items."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = items
    session.execute.return_value = mock_result


def mock_scalar_count(count: int, *, session: AsyncMock):
    """Mock session.execute() to return scalar_one() with a count value."""
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = count
    session.execute.return_value = mock_result


def mock_paginated_result(items: list, total: int, *, session: AsyncMock):
    """Mock session.execute() for paginated queries (count + select)."""
    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = items

    session.execute = AsyncMock(side_effect=[count_result, items_result])


def make_video(**kwargs):
    """Create a mock Video with sensible defaults for testing."""
    defaults = dict(
        id=VIDEO_ID,
        script_text="hello",
        status=VideoStatus.processing,
        current_stage=VideoStage.queued,
        batch_id=None,
        error_message=None,
        output_url=None,
        model_costs={},
        total_cost_usd=0.0,
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


def make_video_crud(video):
    """Create a mock VideoCrud that copies input fields onto the video."""
    crud = AsyncMock()

    async def create_side_effect(video_input):
        for field, value in video_input.model_dump(exclude_unset=True).items():
            setattr(video, field, value)
        return video

    crud.create.side_effect = create_side_effect
    return crud


def make_mock_providers(**overrides) -> PipelineProviders:
    """Create a PipelineProviders with mock implementations.

    Uses model_construct to skip Pydantic validation — mocks don't pass isinstance checks.
    """
    return PipelineProviders.model_construct(
        tts=overrides.get("tts", MagicMock(spec=TTSService)),
        segmentation=overrides.get("segmentation", AsyncMock(spec=SegmentationService)),
        image_gen=overrides.get("image_gen", MagicMock(spec=ImageGenService)),
        editor=overrides.get("editor", MagicMock(spec=VideoEditor)),
    )


def build_service(**overrides) -> VideoService:
    """Build a VideoService with mock dependencies."""
    providers = make_mock_providers(
        tts=overrides.pop("tts", MagicMock(spec=TTSService)),
        segmentation=overrides.pop("segmentation", AsyncMock(spec=SegmentationService)),
        image_gen=overrides.pop("image_gen", MagicMock(spec=ImageGenService)),
        editor=overrides.pop("editor", MagicMock(spec=VideoEditor)),
    )
    defaults = dict(
        session=AsyncMock(spec=AsyncSession),
        storage=MagicMock(spec=StorageService),
        events=AsyncMock(spec=EventService),
        app_settings=AsyncMock(spec=AppSettingsCrud),
        video_crud=AsyncMock(spec=VideoCrud),
        providers=providers,
    )
    defaults.update(overrides)
    return VideoService(**defaults)


def make_tts_result():
    """Create a mock TTS result for tests that don't reach assembly."""
    return MagicMock(
        audio_s3_key="k",
        audio_duration_ms=1000,
        word_timestamps=[],
        cost=MagicMock(cost_usd=0.01, token_count=0),
    )


def make_real_tts_result() -> TTSResult:
    """Create a real TTSResult with actual bytes for tests that reach assembly."""
    return TTSResult(
        audio_bytes=b"fake-audio-data",
        content_type="audio/mpeg",
        audio_duration_ms=1000,
        word_timestamps=[],
        cost=AICost(cost_usd=0.01, token_count=0),
    )


def make_mock_segment():
    """Create a realistic mock segment for pipeline tests."""
    seg = MagicMock()
    seg.order = 0
    seg.image_prompt = "A vivid scene"
    seg.text = "hello world"
    seg.start_time = 0.0
    seg.end_time = 5.0
    seg.effect = MagicMock()
    seg.effect.model_dump.return_value = {
        "type": "ken_burns",
        "direction": "zoom_in",
        "scale": 1.2,
    }
    return seg


def make_seg_result(*, segments=None):
    """Create a mock segmentation result."""
    result = MagicMock()
    result.segments = segments or []
    result.prompt = "test"
    result.tokens_used = 10
    result.cost_usd = 0.001
    return result
