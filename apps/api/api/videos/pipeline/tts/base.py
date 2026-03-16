"""Abstract TTS service."""

from abc import ABC, abstractmethod
from uuid import UUID

from api.videos.pipeline.tts.schemas import TTSResult


class TTSService(ABC):
    """Abstract TTS provider — subclass for different providers."""

    @abstractmethod
    def synthesize(
        self, script_text: str, voice_id: str | None, video_id: UUID
    ) -> TTSResult:
        """Convert script text to speech audio with word-level timestamps."""
        ...
