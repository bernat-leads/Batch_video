"""Tests for shot PATCH endpoint — update, 404 on bad ID, mismatched video_id."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _mock_shot(**kwargs) -> MagicMock:
    """Build a mock Shot with sensible defaults."""
    from datetime import datetime

    defaults = dict(
        id=uuid.uuid4(),
        video_id=uuid.uuid4(),
        order=0,
        text="Shot text",
        image_prompt="A vivid scene",
        effect_config=None,
        start_time=0.0,
        end_time=5.0,
        image_url=None,
        cost_usd=0.0,
        created_at=datetime(2025, 1, 1),
        updated_at=None,
    )
    defaults.update(kwargs)
    shot = MagicMock()
    for key, value in defaults.items():
        setattr(shot, key, value)
    return shot


class TestUpdateShot:
    """PATCH /videos/{video_id}/shots/{shot_id} updates the shot."""

    def test_updates_image_prompt(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        shot_id = uuid.uuid4()
        original = _mock_shot(id=shot_id, video_id=video_id)
        updated = _mock_shot(
            id=shot_id,
            video_id=video_id,
            image_prompt="A new prompt",
        )

        with (
            patch(
                "api.shots.crud.ShotCrud.get",
                new_callable=AsyncMock,
                return_value=original,
            ),
            patch(
                "api.shots.crud.ShotCrud.update",
                new_callable=AsyncMock,
                return_value=updated,
            ),
        ):
            resp = authed_client.patch(
                f"/api/v1/videos/{video_id}/shots/{shot_id}",
                json={"image_prompt": "A new prompt"},
            )

        assert resp.status_code == 200
        assert resp.json()["image_prompt"] == "A new prompt"

    def test_updates_multiple_fields(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        shot_id = uuid.uuid4()
        original = _mock_shot(id=shot_id, video_id=video_id)
        updated = _mock_shot(
            id=shot_id,
            video_id=video_id,
            text="New text",
            start_time=1.5,
        )

        with (
            patch(
                "api.shots.crud.ShotCrud.get",
                new_callable=AsyncMock,
                return_value=original,
            ),
            patch(
                "api.shots.crud.ShotCrud.update",
                new_callable=AsyncMock,
                return_value=updated,
            ),
        ):
            resp = authed_client.patch(
                f"/api/v1/videos/{video_id}/shots/{shot_id}",
                json={"text": "New text", "start_time": 1.5},
            )

        assert resp.status_code == 200
        assert resp.json()["text"] == "New text"
        assert resp.json()["start_time"] == 1.5


class TestUpdateShotNotFound:
    """PATCH returns 404 when shot_id does not exist."""

    def test_returns_404_for_invalid_shot_id(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        shot_id = uuid.uuid4()

        with patch(
            "api.shots.crud.ShotCrud.get",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = authed_client.patch(
                f"/api/v1/videos/{video_id}/shots/{shot_id}",
                json={"image_prompt": "A new prompt"},
            )

        assert resp.status_code == 404


class TestUpdateShotMismatchedVideoId:
    """PATCH returns 404 when shot belongs to a different video."""

    def test_returns_404_for_mismatched_video_id(self, authed_client: TestClient):
        video_id = uuid.uuid4()
        other_video_id = uuid.uuid4()
        shot_id = uuid.uuid4()

        # Shot exists but belongs to a different video
        shot = _mock_shot(id=shot_id, video_id=other_video_id)

        with patch(
            "api.shots.crud.ShotCrud.get",
            new_callable=AsyncMock,
            return_value=shot,
        ):
            resp = authed_client.patch(
                f"/api/v1/videos/{video_id}/shots/{shot_id}",
                json={"image_prompt": "A new prompt"},
            )

        assert resp.status_code == 404
