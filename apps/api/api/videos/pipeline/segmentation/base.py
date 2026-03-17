"""Abstract segmentation service."""

from abc import ABC, abstractmethod

from api.videos.pipeline.segmentation.schemas import (
    SegmentationInput,
    SegmentationResult,
)


class SegmentationService(ABC):
    """Abstract segmentation provider — subclass for different LLMs."""

    @abstractmethod
    async def segment_script(
        self, segmentation_input: SegmentationInput
    ) -> SegmentationResult:
        """Split script into visual segments with image prompts and Ken Burns directions."""
        ...
