"""Abstract TTS service."""

from abc import ABC, abstractmethod

from api.videos.pipeline.tts.schemas import TTSInput, TTSResult


class TTSService(ABC):
    """Abstract TTS provider — subclass for different providers."""

    @abstractmethod
    def synthesize(self, tts_input: TTSInput) -> TTSResult:
        """Convert script text to speech audio with word-level timestamps."""
        ...
