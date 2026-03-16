"""Tests for ShotService edge cases."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.shots.service import ShotService
from api.videos.pipeline.segmentation.schemas import (
    KenBurnsConfig,
    KenBurnsDirection,
    SegmentWithTiming,
)


def _segment(order=1):
    return SegmentWithTiming(
        order=order,
        text="test segment",
        image_prompt="a beautiful scene",
        ken_burns_config=KenBurnsConfig(direction=KenBurnsDirection.zoom_in, scale=1.2),
        start_time=0.0,
        end_time=5.0,
    )


def _image_result():
    return MagicMock(
        image_bytes=b"fake-png", content_type="image/png", cost=MagicMock(cost_usd=0.05)
    )


class TestStorageUploadFailure:
    @pytest.mark.asyncio
    async def test_upload_error_propagates(self):
        session = AsyncMock()
        session.add = MagicMock()
        storage = MagicMock()
        storage.upload_file.side_effect = OSError("R2 timeout")

        service = ShotService(session, storage, MagicMock())

        with pytest.raises(OSError, match="R2 timeout"):
            await service.create_shot_with_image(uuid.uuid4(), _segment(), _image_result())


class TestSuccessfulShot:
    @pytest.mark.asyncio
    async def test_returns_shot_with_r2_key_and_cost(self):
        session = AsyncMock()
        session.add = MagicMock()
        storage = MagicMock()

        service = ShotService(session, storage, MagicMock())
        vid = uuid.uuid4()
        shot = await service.create_shot_with_image(vid, _segment(order=3), _image_result())

        assert shot.image_url == f"videos/{vid}/shots/003.png"
        assert shot.cost_usd == 0.05
        storage.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_shot_flushed_to_db(self):
        """Shot should be flushed to DB before R2 upload."""
        session = AsyncMock()
        session.add = MagicMock()
        storage = MagicMock()

        service = ShotService(session, storage, MagicMock())
        await service.create_shot_with_image(uuid.uuid4(), _segment(), _image_result())

        session.flush.assert_called_once()
