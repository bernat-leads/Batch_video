"""Tests for Video live total_cost_usd — computed from model_costs JSON, not stored."""

import pytest

from api.videos.models.video import Video


class TestVideoModelHasComputedTotalCost:
    """total_cost_usd should be a column_property, not a stored column."""

    def test_total_cost_usd_not_in_table_columns(self):
        """total_cost_usd should NOT be a real table column."""
        mapped_columns = {col.key for col in Video.__table__.columns}
        assert "total_cost_usd" not in mapped_columns

    def test_total_cost_usd_is_accessible(self):
        """total_cost_usd should be accessible as an attribute on Video."""
        assert hasattr(Video, "total_cost_usd")

    def test_model_costs_is_stored_column(self):
        """model_costs should remain a real stored column."""
        mapped_columns = {col.key for col in Video.__table__.columns}
        assert "model_costs" in mapped_columns


class TestRecordModelCost:
    """record_model_cost should accumulate costs in model_costs JSON."""

    def test_adds_new_model(self):
        video = Video(script_text="test", voice_id="v1")
        video.model_costs = {}
        video.record_model_cost("claude-sonnet", cost_usd=0.01, token_count=100)

        assert "claude-sonnet" in video.model_costs
        assert video.model_costs["claude-sonnet"]["cost_usd"] == 0.01
        assert video.model_costs["claude-sonnet"]["token_count"] == 100

    def test_accumulates_existing_model(self):
        video = Video(script_text="test", voice_id="v1")
        video.model_costs = {}
        video.record_model_cost("imagen", cost_usd=0.01, token_count=1)
        video.record_model_cost("imagen", cost_usd=0.01, token_count=1)

        assert video.model_costs["imagen"]["cost_usd"] == pytest.approx(0.02)
        assert video.model_costs["imagen"]["token_count"] == 2

    def test_multiple_models(self):
        video = Video(script_text="test", voice_id="v1")
        video.model_costs = {}
        video.record_model_cost("elevenlabs", cost_usd=0.005, token_count=500)
        video.record_model_cost("claude-sonnet", cost_usd=0.02, token_count=1000)
        video.record_model_cost("imagen", cost_usd=0.03, token_count=3)

        assert len(video.model_costs) == 3
        assert video.model_costs["elevenlabs"]["cost_usd"] == pytest.approx(0.005)
        assert video.model_costs["claude-sonnet"]["cost_usd"] == pytest.approx(0.02)
        assert video.model_costs["imagen"]["cost_usd"] == pytest.approx(0.03)

    def test_empty_model_costs_starts_clean(self):
        video = Video(script_text="test", voice_id="v1")
        video.model_costs = {}
        assert video.model_costs == {}


class TestRecomputeTotalsRemoved:
    """recompute_totals should no longer exist on Video."""

    def test_no_recompute_totals_method(self):
        assert not hasattr(Video, "recompute_totals")


class TestVideoReadSchemaAcceptsTotalCost:
    """VideoRead should still accept total_cost_usd from the computed property."""

    def test_video_read_has_total_cost_field(self):
        from api.videos.schemas import VideoRead

        assert "total_cost_usd" in VideoRead.model_fields

    def test_video_read_default_zero(self):
        import uuid
        from api.videos.schemas import VideoRead

        video = VideoRead(
            id=uuid.uuid4(),
            script_text="test",
            voice_id="v1",
            status="processing",
            current_stage="queued",
            created_at="2026-01-01T00:00:00",
        )
        assert video.total_cost_usd == 0.0
