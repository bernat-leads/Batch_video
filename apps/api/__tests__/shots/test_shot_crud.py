"""Tests for ShotCrud.get_by_video — retrieves shots ordered by sequence."""

import uuid
from unittest.mock import AsyncMock

import pytest

from __tests__.helpers import fake_db_obj, mock_scalars_result
from api.shots.crud import ShotCrud


@pytest.fixture
def shot_crud(mock_session: AsyncMock) -> ShotCrud:
    """Build a ShotCrud backed by a mocked session."""
    return ShotCrud(session=mock_session)


class TestGetByVideo:
    """Verify ShotCrud.get_by_video returns shots for a given video."""

    async def test_returns_shots_for_video(
        self, shot_crud: ShotCrud, mock_session: AsyncMock
    ):
        video_id = uuid.uuid4()
        shots = [
            fake_db_obj(id=uuid.uuid4(), video_id=video_id, order=0, text="Shot 1"),
            fake_db_obj(id=uuid.uuid4(), video_id=video_id, order=1, text="Shot 2"),
        ]
        mock_scalars_result(shots, session=mock_session)

        result = await shot_crud.get_by_video(video_id)

        assert len(result) == 2
        assert result[0].text == "Shot 1"
        assert result[1].text == "Shot 2"
        mock_session.execute.assert_awaited_once()

    async def test_returns_empty_list_when_no_shots(
        self, shot_crud: ShotCrud, mock_session: AsyncMock
    ):
        mock_scalars_result([], session=mock_session)

        result = await shot_crud.get_by_video(uuid.uuid4())

        assert result == []
