"""Stage 2: Script segmentation."""

from api.videos.pipeline.segmentation.base import SegmentationService
from api.videos.pipeline.segmentation.claude import ClaudeSegmentationService
from api.videos.pipeline.segmentation.schemas import (
    AnySegmentEffect,
    KenBurnsDirection,
    KenBurnsEffect,
    SegmentationInput,
    SegmentationResult,
    SegmentEffect,
    SegmentResult,
)

__all__ = [
    "AnySegmentEffect",
    "ClaudeSegmentationService",
    "KenBurnsDirection",
    "KenBurnsEffect",
    "SegmentEffect",
    "SegmentResult",
    "SegmentationInput",
    "SegmentationResult",
    "SegmentationService",
]
