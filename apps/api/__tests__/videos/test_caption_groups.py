"""Tests for CaptionGroup — quote stripping, sentence-ender stripping, grouping logic."""

import pytest

from api.videos.pipeline.tts.schemas import WordTimestamp
from api.videos.pipeline.video_editor.schemas import CaptionGroup


class TestQuoteStripping:
    """Captions should strip quotation marks from word timestamps."""

    @pytest.mark.parametrize(
        "words, expected_text",
        [
            pytest.param(
                ['"Hello', 'world"'],
                "Hello world",
                id="straight-double-quotes",
            ),
            pytest.param(
                ['\u201cHello', 'world\u201d'],
                "Hello world",
                id="curly-double-quotes",
            ),
            pytest.param(
                ['\u00abHello', 'world\u00bb'],
                "Hello world",
                id="guillemets",
            ),
            pytest.param(
                ['\u2018Hello', 'world\u2019'],
                "Hello world",
                id="curly-single-quotes",
            ),
            pytest.param(
                ["Hello", "world"],
                "Hello world",
                id="no-quotes-unchanged",
            ),
            pytest.param(
                ['"Hello"'],
                "Hello",
                id="word-wrapped-in-quotes",
            ),
        ],
    )
    def test_quotes_stripped_from_captions(self, words, expected_text):
        timestamps = [
            WordTimestamp(word=w, start=i * 0.5, end=(i + 1) * 0.5)
            for i, w in enumerate(words)
        ]
        groups = CaptionGroup.from_word_timestamps(timestamps, max_chars=50)
        assert len(groups) >= 1
        assert groups[0].text == expected_text


class TestSentenceEnderStripping:
    """Sentence-ending punctuation (.!?) should be stripped from display."""

    @pytest.mark.parametrize(
        "words, expected_text",
        [
            pytest.param(["Hello."], "Hello", id="period"),
            pytest.param(["Hello!"], "Hello", id="exclamation"),
            pytest.param(["Hello?"], "Hello", id="question"),
            pytest.param(["Hello,"], "Hello,", id="comma-kept"),
        ],
    )
    def test_sentence_enders_stripped(self, words, expected_text):
        timestamps = [
            WordTimestamp(word=w, start=0.0, end=0.5)
            for w in words
        ]
        groups = CaptionGroup.from_word_timestamps(timestamps, max_chars=50)
        assert groups[0].text == expected_text


class TestGroupTiming:
    """Caption groups should have correct start/end times."""

    def test_single_word_timing(self):
        timestamps = [WordTimestamp(word="Hello", start=1.0, end=1.5)]
        groups = CaptionGroup.from_word_timestamps(timestamps, max_chars=50)
        assert len(groups) == 1
        assert groups[0].start == 1.0
        assert groups[0].end == 1.5

    def test_groups_extended_to_next_start(self):
        """Each group's end should extend to the next group's start (no blank frames)."""
        timestamps = [
            WordTimestamp(word="Hello", start=0.0, end=0.5),
            WordTimestamp(word="world.", start=0.6, end=1.0),
            WordTimestamp(word="Goodbye", start=2.0, end=2.5),
        ]
        groups = CaptionGroup.from_word_timestamps(timestamps, max_chars=50)
        # Should break at sentence boundary after "world."
        assert len(groups) >= 2
        # First group's end should extend to second group's start
        assert groups[0].end == groups[1].start

    def test_empty_words_returns_empty(self):
        assert CaptionGroup.from_word_timestamps([], max_chars=50) == []


class TestGroupBreaking:
    """Groups should break on pauses, sentence boundaries, and length limits."""

    def test_breaks_on_sentence_boundary(self):
        timestamps = [
            WordTimestamp(word="Hello.", start=0.0, end=0.5),
            WordTimestamp(word="World", start=0.6, end=1.0),
        ]
        groups = CaptionGroup.from_word_timestamps(timestamps, max_chars=50)
        assert len(groups) == 2
        assert groups[0].text == "Hello"
        assert groups[1].text == "World"

    def test_breaks_on_max_chars(self):
        timestamps = [
            WordTimestamp(word="Hello", start=0.0, end=0.3),
            WordTimestamp(word="beautiful", start=0.3, end=0.6),
            WordTimestamp(word="world", start=0.6, end=0.9),
        ]
        groups = CaptionGroup.from_word_timestamps(timestamps, max_chars=10)
        assert len(groups) >= 2

    def test_breaks_on_max_words(self):
        timestamps = [
            WordTimestamp(word=f"w{i}", start=i * 0.2, end=(i + 1) * 0.2)
            for i in range(6)
        ]
        groups = CaptionGroup.from_word_timestamps(timestamps, max_chars=100, max_words=2)
        assert len(groups) >= 3
