"""OpenAI TTS implementation using gpt-4o-mini-tts with word-level timestamps."""

import logging

from openai import OpenAI

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.videos.pipeline.config import (
    OPENAI_TTS_COST_PER_CHAR,
    OPENAI_TTS_DEFAULT_VOICE,
    OPENAI_TTS_MODEL,
)
from api.videos.pipeline.tts.base import TTSService
from api.videos.pipeline.tts.schemas import TTSInput, TTSResult, WordTimestamp
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class OpenAITTSService(TTSService):
    """OpenAI TTS with word-level timestamps via gpt-4o-mini-tts."""

    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    @pipeline_retry()
    def synthesize(self, tts_input: TTSInput) -> TTSResult:
        """Generate TTS audio with word-level timestamps."""
        effective_voice = tts_input.voice_id or OPENAI_TTS_DEFAULT_VOICE
        logger.info(
            "OpenAI TTS starting (voice=%s, %d chars)",
            effective_voice,
            len(tts_input.script_text),
        )

        try:
            response = self._client.audio.speech.create(
                model=OPENAI_TTS_MODEL,
                voice=effective_voice,
                input=tts_input.script_text,
                response_format="wav",
            )
        except Exception as error:
            raise PipelineStageError(
                "tts", f"OpenAI TTS API call failed: {error}"
            ) from error

        audio_bytes = response.content
        word_timestamps = self._get_word_timestamps(audio_bytes, tts_input.script_text)
        duration_ms = int(word_timestamps[-1].end * 1000) if word_timestamps else 0
        cost_usd = len(tts_input.script_text) * OPENAI_TTS_COST_PER_CHAR

        logger.info(
            "OpenAI TTS complete (%d words, %dms, $%.4f)",
            len(word_timestamps),
            duration_ms,
            cost_usd,
        )

        return TTSResult(
            audio_bytes=audio_bytes,
            content_type="audio/wav",
            audio_duration_ms=duration_ms,
            word_timestamps=word_timestamps,
            cost=AICost(cost_usd=cost_usd),
        )

    def _get_word_timestamps(
        self, audio_bytes: bytes, script_text: str
    ) -> list[WordTimestamp]:
        """Transcribe audio with Whisper to get word-level timestamps."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            transcript = self._client.audio.transcriptions.create(
                model="whisper-1",
                file=Path(tmp_path),
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        except Exception as error:
            logger.warning("Failed to get word timestamps via Whisper: %s", error)
            return self._fallback_timestamps(script_text, audio_bytes)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        words: list[WordTimestamp] = []
        if hasattr(transcript, "words") and transcript.words:
            for word in transcript.words:
                words.append(
                    WordTimestamp(
                        word=word.word.strip(), start=word.start, end=word.end
                    )
                )
        elif words_data := getattr(transcript, "words", None):
            for word in words_data:
                words.append(
                    WordTimestamp(
                        word=word["word"].strip(),
                        start=word["start"],
                        end=word["end"],
                    )
                )

        if not words:
            return self._fallback_timestamps(script_text, audio_bytes)

        return words

    @staticmethod
    def _fallback_timestamps(
        script_text: str, audio_bytes: bytes
    ) -> list[WordTimestamp]:
        """Estimate word timestamps by distributing evenly across audio duration."""
        import struct

        try:
            byte_rate = struct.unpack_from("<I", audio_bytes, 28)[0]
            data_size = len(audio_bytes) - 44
            duration = data_size / byte_rate if byte_rate > 0 else 0
        except Exception:
            duration = len(script_text) * 0.06

        raw_words = script_text.split()
        if not raw_words:
            return []

        word_duration = duration / len(raw_words)
        return [
            WordTimestamp(
                word=word,
                start=round(index * word_duration, 3),
                end=round((index + 1) * word_duration, 3),
            )
            for index, word in enumerate(raw_words)
        ]
