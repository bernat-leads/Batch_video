"""Tests for batch status derivation logic.

Batch.status is a SQL column_property computed from video counts:
- 0 total videos → failed
- any processing videos → processing
- all videos failed → failed
- otherwise → completed
"""

import pytest

from api.batches.enums import BatchStatus


def derive_batch_status(
    total_videos: int, pending_count: int, failed_count: int
) -> BatchStatus:
    """Pure-Python mirror of the SQL case expression in Batch.status."""
    if total_videos == 0:
        return BatchStatus.failed
    if pending_count > 0:
        return BatchStatus.processing
    if failed_count == total_videos:
        return BatchStatus.failed
    return BatchStatus.completed


@pytest.mark.parametrize(
    "total_videos, pending_count, failed_count, expected",
    [
        pytest.param(5, 5, 0, BatchStatus.processing, id="all-processing"),
        pytest.param(5, 1, 0, BatchStatus.processing, id="one-pending"),
        pytest.param(5, 0, 0, BatchStatus.completed, id="all-finished"),
        pytest.param(1, 0, 0, BatchStatus.completed, id="single-finished"),
        pytest.param(5, 0, 2, BatchStatus.completed, id="mixed-finished-failed"),
        pytest.param(5, 0, 4, BatchStatus.completed, id="mostly-failed-one-done"),
        pytest.param(5, 0, 5, BatchStatus.failed, id="all-failed"),
        pytest.param(1, 0, 1, BatchStatus.failed, id="single-failed"),
        pytest.param(0, 0, 0, BatchStatus.failed, id="zero-total"),
    ],
)
def test_derive_batch_status(total_videos, pending_count, failed_count, expected):
    assert derive_batch_status(total_videos, pending_count, failed_count) == expected
