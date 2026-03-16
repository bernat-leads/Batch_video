"""Abstract segmentation service."""

from abc import ABC, abstractmethod

from api.videos.pipeline.segmentation.schemas import SegmentationResult
from api.videos.pipeline.tts.schemas import WordTimestamp


class SegmentationService(ABC):
    """Abstract segmentation provider — subclass for different LLMs."""

    @abstractmethod
    async def segment_script(
        self,
        script_text: str,
        word_timestamps: list[WordTimestamp],
        style: str | None,
        prompt: str,
    ) -> SegmentationResult:
        """Split script into visual segments with image prompts and Ken Burns directions."""
        ...
