"""Tests for enum consistency — catch mismatches between video/batch status values."""

from api.batches.enums import BatchStatus
from api.videos.enums import VideoStage, VideoStatus


class TestVideoStatusValues:
    def test_no_pending_status(self):
        """'pending' was removed — ensure it doesn't exist."""
        values = [s.value for s in VideoStatus]
        assert "pending" not in values

    def test_no_completed_status(self):
        """'completed' was renamed to 'finished' — ensure old value doesn't exist."""
        values = [s.value for s in VideoStatus]
        assert "completed" not in values

    def test_expected_statuses(self):
        assert set(s.value for s in VideoStatus) == {"processing", "finished", "failed"}


class TestVideoStageValues:
    def test_done_stage_exists(self):
        """The final stage must be 'done', not 'completed' or 'finished'."""
        assert VideoStage.done.value == "done"

    def test_stage_order(self):
        """Stages should follow the pipeline order."""
        stages = [s.value for s in VideoStage]
        assert stages == [
            "queued",
            "tts",
            "segmentation",
            "image_generation",
            "assembly",
            "upload",
            "done",
        ]


class TestBatchStatusValues:
    def test_expected_statuses(self):
        assert set(s.value for s in BatchStatus) == {
            "processing",
            "completed",
            "failed",
        }
