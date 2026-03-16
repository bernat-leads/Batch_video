"""OpenAI TTS implementation using gpt-4o-mini-tts with word-level timestamps."""

import logging
from uuid import UUID

from openai import OpenAI

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.storage import StorageService
from api.videos.pipeline.tts.base import TTSService
from api.videos.pipeline.tts.schemas import TTSResult, WordTimestamp
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)

# OpenAI TTS pricing (per 1M characters)
# gpt-4o-mini-tts: $12/1M chars → $0.000012/char
OPENAI_TTS_COST_PER_CHAR = 0.000012


class OpenAITTSService(TTSService):
    """OpenAI TTS with word-level timestamps via gpt-4o-mini-tts."""

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    @pipeline_retry()
    def synthesize(
        self, script_text: str, voice_id: str | None, video_id: UUID
    ) -> TTSResult:
        """Generate TTS audio with word-level timestamps and upload to R2."""
        effective_voice = voice_id or settings.OPENAI_TTS_DEFAULT_VOICE
        logger.info(
            "Video %s: OpenAI TTS starting (voice=%s, %d chars)",
            video_id,
            effective_voice,
            len(script_text),
        )

        try:
            response = self._client.audio.speech.create(
                model=settings.OPENAI_TTS_MODEL,
                voice=effective_voice,
                input=script_text,
                response_format="wav",
            )
        except Exception as e:
            raise PipelineStageError("tts", f"OpenAI TTS API call failed: {e}") from e

        audio_bytes = response.content

        # Get word-level timestamps via transcription
        word_timestamps = self._get_word_timestamps(audio_bytes, script_text)

        r2_key = f"videos/{video_id}/audio.wav"
        self._storage.upload_file(r2_key, audio_bytes, "audio/wav")

        duration_ms = int(word_timestamps[-1].end * 1000) if word_timestamps else 0
        cost_usd = len(script_text) * OPENAI_TTS_COST_PER_CHAR

        logger.info(
            "Video %s: OpenAI TTS complete (%d words, %dms, $%.4f)",
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

    def _get_word_timestamps(
        self, audio_bytes: bytes, script_text: str
    ) -> list[WordTimestamp]:
        """Transcribe audio with Whisper to get word-level timestamps."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            transcript = self._client.audio.transcriptions.create(
                model="whisper-1",
                file=Path(tmp_path),
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        except Exception as e:
            logger.warning("Failed to get word timestamps via Whisper: %s", e)
            return self._fallback_timestamps(script_text, audio_bytes)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        words: list[WordTimestamp] = []
        if hasattr(transcript, "words") and transcript.words:
            for w in transcript.words:
                words.append(
                    WordTimestamp(word=w.word.strip(), start=w.start, end=w.end)
                )
        elif words_data := getattr(transcript, "words", None):
            for w in words_data:
                words.append(
                    WordTimestamp(
                        word=w["word"].strip(),
                        start=w["start"],
                        end=w["end"],
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

        # Parse WAV header to get duration
        try:
            # WAV: bytes 24-28 = sample rate, bytes 28-32 = byte rate
            byte_rate = struct.unpack_from("<I", audio_bytes, 28)[0]
            data_size = len(audio_bytes) - 44  # subtract header
            duration = data_size / byte_rate if byte_rate > 0 else 0
        except Exception:
            duration = len(script_text) * 0.06  # ~60ms per character estimate

        raw_words = script_text.split()
        if not raw_words:
            return []

        word_duration = duration / len(raw_words)
        return [
            WordTimestamp(
                word=w,
                start=round(i * word_duration, 3),
                end=round((i + 1) * word_duration, 3),
            )
            for i, w in enumerate(raw_words)
        ]
