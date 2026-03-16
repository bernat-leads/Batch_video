"""ElevenLabs TTS implementation."""

import base64
import logging
from uuid import UUID

from elevenlabs import ElevenLabs

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.storage import StorageService
from api.videos.pipeline.config import TTS_COST_PER_CHAR
from api.videos.pipeline.tts.base import TTSService
from api.videos.pipeline.tts.schemas import TTSResult, WordTimestamp
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class ElevenLabsTTSService(TTSService):
    """ElevenLabs TTS with word-level timestamps."""

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage
        self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    @pipeline_retry()
    def synthesize(
        self, script_text: str, voice_id: str | None, video_id: UUID
    ) -> TTSResult:
        """Generate TTS audio with word-level timestamps and upload to R2."""
        effective_voice_id = voice_id or settings.ELEVENLABS_DEFAULT_VOICE_ID
        logger.info(
            "Video %s: TTS starting (voice=%s, %d chars)",
            video_id,
            effective_voice_id,
            len(script_text),
        )

        try:
            response = self._client.text_to_speech.convert_with_timestamps(
                text=script_text,
                voice_id=effective_voice_id,
                model_id=settings.ELEVENLABS_MODEL_ID,
            )
        except Exception as e:
            raise PipelineStageError("tts", f"ElevenLabs API call failed: {e}") from e

        audio_bytes = base64.b64decode(response.audio_base_64)
        word_timestamps = self._parse_word_timestamps(response.alignment)

        r2_key = f"videos/{video_id}/audio.mp3"
        self._storage.upload_file(r2_key, audio_bytes, "audio/mpeg")

        duration_ms = int(word_timestamps[-1].end * 1000) if word_timestamps else 0
        cost_usd = len(script_text) * TTS_COST_PER_CHAR

        logger.info(
            "Video %s: TTS complete (%d words, %dms, $%.4f)",
            video_id,
            len(word_timestamps),
            duration_ms,
            cost_usd,
        )

        return TTSResult(
            audio_r2_key=r2_key,
            audio_duration_ms=duration_ms,
            word_timestamps=word_timestamps,
            cost=AICost(cost_usd=cost_usd),
        )

    @staticmethod
    def _parse_word_timestamps(alignment) -> list[WordTimestamp]:
        """Convert character-level alignment to word-level timestamps."""
        if not alignment:
            return []

        chars = alignment.characters
        starts = alignment.character_start_times_seconds
        ends = alignment.character_end_times_seconds

        words: list[WordTimestamp] = []
        current_word = ""
        word_start: float | None = None

        for i, char in enumerate(chars):
            if char == " ":
                if current_word and word_start is not None:
                    words.append(
                        WordTimestamp(
                            word=current_word, start=word_start, end=ends[i - 1]
                        )
                    )
                current_word = ""
                word_start = None
            else:
                if word_start is None:
                    word_start = starts[i]
                current_word += char

        if current_word and word_start is not None:
            words.append(
                WordTimestamp(word=current_word, start=word_start, end=ends[-1])
            )

        return words
