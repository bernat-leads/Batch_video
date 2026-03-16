"""Abstract video template."""

from abc import ABC, abstractmethod

from api.videos.pipeline.video_editor.schemas import CaptionWord, EditResult, Segment


class VideoTemplate(ABC):
    """Abstract video template — subclass for different editing backends and styles."""

    @abstractmethod
    def assemble_video(
        self,
        segments: list[Segment],
        audio_bytes: bytes,
        captions: list[CaptionWord],
        top_text: str | None = None,
    ) -> EditResult:
        """Assemble final video from image segments, audio, and captions."""
        ...
