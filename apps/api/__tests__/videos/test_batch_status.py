"""Tests for Batch.derive_status() — all combinations via parametrize."""

from unittest.mock import MagicMock

import pytest

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


@pytest.mark.parametrize(
    "counts, expected",
    [
        # (completed, failed, pending, total) → expected status
        pytest.param(dict(pending_count=5, total_videos=5), BatchStatus.processing, id="all-processing"),
        pytest.param(dict(completed_count=4, pending_count=1, total_videos=5), BatchStatus.processing, id="one-pending"),
        pytest.param(dict(completed_count=5, total_videos=5), BatchStatus.completed, id="all-finished"),
        pytest.param(dict(completed_count=1, total_videos=1), BatchStatus.completed, id="single-finished"),
        pytest.param(dict(completed_count=3, failed_count=2, total_videos=5), BatchStatus.completed, id="mixed-finished-failed"),
        pytest.param(dict(completed_count=1, failed_count=4, total_videos=5), BatchStatus.completed, id="mostly-failed-one-done"),
        pytest.param(dict(failed_count=5, total_videos=5), BatchStatus.failed, id="all-failed"),
        pytest.param(dict(failed_count=1, total_videos=1), BatchStatus.failed, id="single-failed"),
        pytest.param(dict(total_videos=0), BatchStatus.failed, id="zero-total"),
    ],
)
def test_derive_status(counts, expected):
    assert _fake_batch(**counts).derive_status() == expected
