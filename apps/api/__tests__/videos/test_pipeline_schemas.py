"""Tests for pipeline schema logic — computed properties and builders."""

import pytest

from api.videos.pipeline.image_generation.schemas import ImageConfig
from api.videos.pipeline.tts.schemas import WordTimestamp


class TestImageConfigDimensions:
    @pytest.mark.parametrize(
        "aspect_ratio, size, expected",
        [
            pytest.param("9:16", "1K", (576, 1024), id="9:16-1K"),
            pytest.param("16:9", "1K", (1024, 576), id="16:9-1K"),
            pytest.param("1:1", "1K", (1024, 1024), id="1:1-1K"),
            pytest.param("9:16", "2K", (1152, 2048), id="9:16-2K"),
            pytest.param("9:16", "4K", (576, 1024), id="unknown-size-fallback"),
            pytest.param("21:9", "1K", (576, 1024), id="unknown-ratio-fallback"),
        ],
    )
    def test_dimensions(self, aspect_ratio, size, expected):
        config = ImageConfig(aspect_ratio=aspect_ratio, size=size)
        assert config.dimensions == expected


class TestWordTimestampToIndexedStr:
    @pytest.mark.parametrize(
        "word, start, end, index, expected_parts",
        [
            pytest.param("Hello", 0.0, 0.5, 0, ["[0]", "Hello", "0.00s", "0.50s"], id="first-word"),
            pytest.param("World", 1.25, 1.75, 42, ["[42]", "World"], id="higher-index"),
        ],
    )
    def test_format_includes_expected_parts(self, word, start, end, index, expected_parts):
        result = WordTimestamp(word=word, start=start, end=end).to_indexed_str(index)
        for part in expected_parts:
            assert part in result
