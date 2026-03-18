"""Tests for enum consistency — catch mismatches between video/batch status values."""

import pytest

from api.batches.enums import BatchStatus
from api.videos.enums import VideoStage, VideoStatus


@pytest.mark.parametrize("removed_value", ["pending", "completed"])
def test_video_status_excludes_removed_values(removed_value):
    """Ensure removed status values don't reappear."""
    assert removed_value not in {s.value for s in VideoStatus}


def test_video_status_expected_values():
    assert {s.value for s in VideoStatus} == {"processing", "finished", "failed"}


def test_batch_status_expected_values():
    assert {s.value for s in BatchStatus} == {"processing", "completed", "failed"}


def test_video_stage_pipeline_order():
    """Stages must follow the pipeline order."""
    assert [s.value for s in VideoStage] == [
        "queued", "tts", "segmentation", "image_generation", "assembly", "upload", "done",
    ]
