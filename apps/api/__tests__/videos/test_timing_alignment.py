"""Tests for word-index-based segment resolution."""

from api.videos.pipeline.segmentation.claude import _resolve_segments
from api.videos.pipeline.segmentation.schemas import (
    KenBurnsConfig,
    KenBurnsDirection,
    SegmentResult,
)
from api.videos.pipeline.tts.schemas import WordTimestamp

_KB = KenBurnsConfig(direction=KenBurnsDirection.zoom_in, scale=1.2)


def _seg(order: int, start: int, end: int) -> SegmentResult:
    return SegmentResult(
        order=order,
        start_word_index=start,
        end_word_index=end,
        image_prompt="prompt",
        ken_burns_config=_KB,
    )


def _word(word: str, start: float, end: float) -> WordTimestamp:
    return WordTimestamp(word=word, start=start, end=end)


class TestResolveSegments:
    def test_single_segment_covers_all_words(self):
        words = [_word("hello", 0.0, 0.5), _word("world", 0.5, 1.0)]
        segments = [_seg(1, 0, 1)]

        result = _resolve_segments(segments, words)

        assert len(result) == 1
        assert result[0].text == "hello world"
        assert result[0].start_time == 0.0
        assert result[0].end_time == 1.0

    def test_two_segments_split_words(self):
        words = [
            _word("hello", 0.0, 0.5),
            _word("world", 0.5, 1.0),
            _word("foo", 1.0, 1.5),
            _word("bar", 1.5, 2.0),
        ]
        segments = [_seg(1, 0, 1), _seg(2, 2, 3)]

        result = _resolve_segments(segments, words)

        assert result[0].text == "hello world"
        assert result[0].start_time == 0.0
        assert result[0].end_time == 1.0
        assert result[1].text == "foo bar"
        assert result[1].start_time == 1.0
        assert result[1].end_time == 2.0

    def test_single_word_segment(self):
        words = [_word("hello", 0.0, 0.5), _word("world", 0.6, 1.0)]
        segments = [_seg(1, 0, 0), _seg(2, 1, 1)]

        result = _resolve_segments(segments, words)

        assert result[0].text == "hello"
        assert result[0].start_time == 0.0
        assert result[0].end_time == 0.5
        assert result[1].text == "world"
        assert result[1].start_time == 0.6
        assert result[1].end_time == 1.0

    def test_clamps_out_of_bounds_indices(self):
        words = [_word("hello", 0.0, 0.5), _word("world", 0.5, 1.0)]
        segments = [_seg(1, -1, 99)]  # way out of range

        result = _resolve_segments(segments, words)

        assert result[0].text == "hello world"
        assert result[0].start_time == 0.0
        assert result[0].end_time == 1.0

    def test_preserves_segment_fields(self):
        words = [_word("hello", 1.5, 2.0)]
        segments = [_seg(1, 0, 0)]

        result = _resolve_segments(segments, words)

        assert result[0].order == 1
        assert result[0].image_prompt == "prompt"
        assert result[0].ken_burns_config == _KB

    def test_start_equals_end_index(self):
        """Segment spanning exactly one word via same start and end index."""
        words = [_word("a", 0.0, 0.1), _word("b", 0.2, 0.3), _word("c", 0.4, 0.5)]
        segments = [_seg(1, 1, 1)]

        result = _resolve_segments(segments, words)

        assert result[0].text == "b"
        assert result[0].start_time == 0.2
        assert result[0].end_time == 0.3
