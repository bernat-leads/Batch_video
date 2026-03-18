"""ElevenLabs TTS implementation."""

import base64
import logging

from elevenlabs import ElevenLabs

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.videos.pipeline.config import ELEVENLABS_MODEL_ID
from api.videos.pipeline.costs import get_tts_char_cost
from api.videos.pipeline.rate_limiter import elevenlabs_limiter, wait_for_slot
from api.videos.pipeline.tts.base import TTSService
from api.videos.pipeline.tts.schemas import TTSInput, TTSResult, WordTimestamp
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class ElevenLabsTTSService(TTSService):
    """ElevenLabs TTS with word-level timestamps."""

    def __init__(self) -> None:
        self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    def synthesize(self, tts_input: TTSInput) -> TTSResult:
        """Generate TTS audio with word-level timestamps."""
        wait_for_slot(elevenlabs_limiter, "elevenlabs:tts")
        return self._call_api(tts_input)

    @pipeline_retry()
    def _call_api(self, tts_input: TTSInput) -> TTSResult:
        """Call the ElevenLabs API (retries on transient errors)."""
        logger.info(
            "ElevenLabs TTS starting (voice=%s, %d chars)",
            tts_input.voice_id,
            len(tts_input.script_text),
        )

        try:
            response = self._client.text_to_speech.convert_with_timestamps(
                text=tts_input.script_text,
                voice_id=tts_input.voice_id,
                model_id=ELEVENLABS_MODEL_ID,
            )
        except Exception as error:
            raise PipelineStageError(
                "tts", f"ElevenLabs API call failed: {error}"
            ) from error

        audio_bytes = base64.b64decode(response.audio_base_64)
        word_timestamps = self._parse_word_timestamps(response.alignment)
        duration_ms = int(word_timestamps[-1].end * 1000) if word_timestamps else 0

        # Character count from alignment = actual characters billed
        char_count = (
            len(response.alignment.characters)
            if response.alignment and response.alignment.characters
            else len(tts_input.script_text)
        )
        cost_usd = char_count * get_tts_char_cost(ELEVENLABS_MODEL_ID)

        logger.info(
            "ElevenLabs TTS complete (%d words, %d chars, %dms, $%.4f)",
            len(word_timestamps),
            char_count,
            duration_ms,
            cost_usd,
        )

        return TTSResult(
            audio_bytes=audio_bytes,
            content_type="audio/mpeg",
            audio_duration_ms=duration_ms,
            word_timestamps=word_timestamps,
            cost=AICost(cost_usd=cost_usd, token_count=char_count),
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

        for index, char in enumerate(chars):
            if char == " ":
                if current_word and word_start is not None:
                    words.append(
                        WordTimestamp(
                            word=current_word, start=word_start, end=ends[index - 1]
                        )
                    )
                current_word = ""
                word_start = None
            else:
                if word_start is None:
                    word_start = starts[index]
                current_word += char

        if current_word and word_start is not None:
            words.append(
                WordTimestamp(word=current_word, start=word_start, end=ends[-1])
            )

        return words
