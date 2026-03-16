"""Stage 2: Script segmentation."""

from api.videos.pipeline.segmentation.base import SegmentationService
from api.videos.pipeline.segmentation.claude import ClaudeSegmentationService
from api.videos.pipeline.segmentation.schemas import (
    KenBurnsConfig,
    KenBurnsDirection,
    SegmentationResult,
    SegmentResult,
)

__all__ = [
    "ClaudeSegmentationService",
    "KenBurnsConfig",
    "KenBurnsDirection",
    "SegmentResult",
    "SegmentationResult",
    "SegmentationService",
]
