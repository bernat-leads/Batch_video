"""Tests for ShotStatus enum and Shot model status field."""

import pytest

from api.shots.enums import ShotStatus


class TestShotStatusTransitions:
    """Shot status should follow: pending → generating → generated/failed."""

    def test_initial_status_is_pending(self):
        assert ShotStatus.pending.value == "pending"

    def test_valid_transitions(self):
        """All expected status values exist."""
        assert ShotStatus.pending == "pending"
        assert ShotStatus.generating == "generating"
        assert ShotStatus.generated == "generated"
        assert ShotStatus.failed == "failed"

    def test_status_is_string_enum(self):
        """ShotStatus values are strings (for DB storage)."""
        for status in ShotStatus:
            assert isinstance(status.value, str)


class TestShotReadSchema:
    """ShotRead should include status and error_message fields."""

    def test_schema_has_status_field(self):
        from api.shots.schemas import ShotRead

        fields = ShotRead.model_fields
        assert "status" in fields
        assert "error_message" in fields

    def test_default_status_is_pending(self):
        import uuid
        from api.shots.schemas import ShotRead

        shot = ShotRead(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            order=0,
            text="hello",
            image_prompt="a cat",
            start_time=0.0,
            end_time=1.0,
            created_at="2026-01-01T00:00:00",
        )
        assert shot.status == ShotStatus.pending
        assert shot.error_message is None
