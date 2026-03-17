"""TTS schemas."""

from pydantic import BaseModel

from api.core.schemas import AICost


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float

    model_config = {"frozen": True}


class TTSResult(BaseModel):
    audio_s3_key: str
    audio_duration_ms: int
    word_timestamps: list[WordTimestamp]
    cost: AICost = AICost()

    model_config = {"frozen": True}
