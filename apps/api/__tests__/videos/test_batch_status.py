"""Tests for Batch.derive_status() edge cases."""

from unittest.mock import MagicMock

from api.batches.enums import BatchStatus
from api.batches.models.batch import Batch


def _fake_batch(*, completed_count=0, failed_count=0, pending_count=0, total_videos=0):
    b = MagicMock(spec=Batch)
    b.completed_count = completed_count
    b.failed_count = failed_count
    b.pending_count = pending_count
    b.total_videos = total_videos
    b.derive_status = lambda: Batch.derive_status(b)
    return b


class TestDeriveBatchStatus:
    def test_all_processing_returns_processing(self):
        assert (
            _fake_batch(pending_count=5, total_videos=5).derive_status()
            == BatchStatus.processing
        )

    def test_all_finished_returns_completed(self):
        assert (
            _fake_batch(completed_count=5, total_videos=5).derive_status()
            == BatchStatus.completed
        )

    def test_all_failed_returns_failed(self):
        assert (
            _fake_batch(failed_count=5, total_videos=5).derive_status()
            == BatchStatus.failed
        )

    def test_mixed_finished_and_failed_returns_completed(self):
        assert (
            _fake_batch(
                completed_count=3, failed_count=2, total_videos=5
            ).derive_status()
            == BatchStatus.completed
        )

    def test_one_still_pending_returns_processing(self):
        assert (
            _fake_batch(
                completed_count=4, pending_count=1, total_videos=5
            ).derive_status()
            == BatchStatus.processing
        )

    def test_zero_total_videos_returns_failed(self):
        assert _fake_batch(total_videos=0).derive_status() == BatchStatus.failed

    def test_single_video_finished(self):
        assert (
            _fake_batch(completed_count=1, total_videos=1).derive_status()
            == BatchStatus.completed
        )

    def test_single_video_failed(self):
        assert (
            _fake_batch(failed_count=1, total_videos=1).derive_status()
            == BatchStatus.failed
        )

    def test_some_failed_some_completed(self):
        assert (
            _fake_batch(
                completed_count=1, failed_count=4, total_videos=5
            ).derive_status()
            == BatchStatus.completed
        )
