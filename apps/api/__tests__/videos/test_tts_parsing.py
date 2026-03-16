"""Tests for ElevenLabs TTS word timestamp parsing edge cases."""

import pytest

from api.videos.pipeline.tts.elevenlabs import ElevenLabsTTSService


def _alignment(chars: list[str], starts: list[float], ends: list[float]):
    """Create a fake alignment object."""

    class FakeAlignment:
        pass

    a = FakeAlignment()
    a.characters = chars
    a.character_start_times_seconds = starts
    a.character_end_times_seconds = ends
    return a


class TestParseWordTimestamps:
    def test_none_alignment_returns_empty(self):
        assert ElevenLabsTTSService._parse_word_timestamps(None) == []

    def test_single_word(self):
        alignment = _alignment(
            ["H", "i"],
            [0.0, 0.1],
            [0.1, 0.2],
        )
        words = ElevenLabsTTSService._parse_word_timestamps(alignment)
        assert len(words) == 1
        assert words[0].word == "Hi"
        assert words[0].start == 0.0
        assert words[0].end == 0.2

    def test_two_words(self):
        alignment = _alignment(
            ["H", "i", " ", "y", "o"],
            [0.0, 0.1, 0.2, 0.3, 0.4],
            [0.1, 0.2, 0.3, 0.4, 0.5],
        )
        words = ElevenLabsTTSService._parse_word_timestamps(alignment)
        assert len(words) == 2
        assert words[0].word == "Hi"
        assert words[1].word == "yo"

    def test_multiple_spaces_between_words(self):
        """Double spaces should not create empty words."""
        alignment = _alignment(
            ["a", " ", " ", "b"],
            [0.0, 0.1, 0.2, 0.3],
            [0.1, 0.2, 0.3, 0.4],
        )
        words = ElevenLabsTTSService._parse_word_timestamps(alignment)
        assert len(words) == 2
        assert words[0].word == "a"
        assert words[1].word == "b"

    def test_trailing_space(self):
        """Trailing space should not create an empty word."""
        alignment = _alignment(
            ["H", "i", " "],
            [0.0, 0.1, 0.2],
            [0.1, 0.2, 0.3],
        )
        words = ElevenLabsTTSService._parse_word_timestamps(alignment)
        assert len(words) == 1
        assert words[0].word == "Hi"

    def test_leading_space(self):
        """Leading space should be skipped."""
        alignment = _alignment(
            [" ", "H", "i"],
            [0.0, 0.1, 0.2],
            [0.1, 0.2, 0.3],
        )
        words = ElevenLabsTTSService._parse_word_timestamps(alignment)
        assert len(words) == 1
        assert words[0].word == "Hi"

    def test_empty_characters_returns_empty(self):
        alignment = _alignment([], [], [])
        words = ElevenLabsTTSService._parse_word_timestamps(alignment)
        assert words == []

    def test_word_timestamps_are_monotonic(self):
        """Each word's start should be >= previous word's end."""
        alignment = _alignment(
            list("Hello World"),
            [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55],
            [0.05, 0.1, 0.15, 0.2, 0.25, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6],
        )
        words = ElevenLabsTTSService._parse_word_timestamps(alignment)
        for i in range(1, len(words)):
            assert words[i].start >= words[i - 1].end
