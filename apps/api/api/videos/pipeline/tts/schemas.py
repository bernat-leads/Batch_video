"""TTS schemas."""

from pydantic import BaseModel, Field

from api.core.schemas import AICost


class WordTimestamp(BaseModel):
    """A single word with TTS timing."""

    word: str = Field(min_length=1)
    start: float = Field(ge=0)
    end: float = Field(ge=0)

    model_config = {"frozen": True}

    def to_indexed_str(self, index: int) -> str:
        """Format as a numbered entry for the segmentation prompt."""
        return f"  [{index}] {self.word} ({self.start:.2f}s–{self.end:.2f}s)"


class TTSInput(BaseModel):
    """Input for the TTS pipeline stage."""

    script_text: str = Field(min_length=1, description="Script text to synthesize")
    voice_id: str = Field(min_length=1, max_length=255, description="TTS voice identifier")

    model_config = {"frozen": True}


class TTSResult(BaseModel):
    """Output of the TTS pipeline stage."""

    audio_bytes: bytes
    content_type: str
    audio_duration_ms: int
    word_timestamps: list[WordTimestamp]
    cost: AICost = AICost()

    model_config = {"frozen": True}
