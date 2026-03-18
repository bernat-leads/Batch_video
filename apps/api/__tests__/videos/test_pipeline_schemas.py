"""Tests for pipeline schema logic — computed properties and builders."""

from api.videos.pipeline.image_generation.schemas import ImageConfig
from api.videos.pipeline.segmentation.schemas import SegmentationInput
from api.videos.pipeline.tts.schemas import WordTimestamp


class TestImageConfigDimensions:
    def test_default_9_16_at_1k(self):
        config = ImageConfig()
        width, height = config.dimensions
        assert width == 576
        assert height == 1024

    def test_16_9_landscape_at_1k(self):
        config = ImageConfig(aspect_ratio="16:9", size="1K")
        width, height = config.dimensions
        assert width == 1024
        assert height == 576

    def test_1_1_square_at_1k(self):
        config = ImageConfig(aspect_ratio="1:1", size="1K")
        width, height = config.dimensions
        assert width == 1024
        assert height == 1024

    def test_9_16_at_2k(self):
        config = ImageConfig(aspect_ratio="9:16", size="2K")
        width, height = config.dimensions
        assert width == 1152
        assert height == 2048

    def test_unknown_size_falls_back_to_1024(self):
        config = ImageConfig(aspect_ratio="9:16", size="4K")
        _, height = config.dimensions
        assert height == 1024

    def test_unknown_aspect_ratio_falls_back_to_9_16(self):
        config = ImageConfig(aspect_ratio="21:9", size="1K")
        width, height = config.dimensions
        assert width == 576
        assert height == 1024


class TestSegmentationInputBuildPrompt:
    def test_base_messages_count(self):
        """System + script + word list = 3 messages."""
        seg_input = SegmentationInput(
            script_text="Hello world",
            word_timestamps=[WordTimestamp(word="Hello", start=0.0, end=0.5)],
            prompt="System prompt",
        )
        messages = seg_input.build_prompt().format_messages()
        assert len(messages) == 3

    def test_style_adds_message(self):
        seg_input = SegmentationInput(
            script_text="Hello", word_timestamps=[], prompt="System",
            style="cinematic dark",
        )
        messages = seg_input.build_prompt().format_messages()
        assert len(messages) == 4

    def test_template_context_adds_message(self):
        seg_input = SegmentationInput(
            script_text="Hello", word_timestamps=[], prompt="System",
            template_context="9:16 vertical",
        )
        messages = seg_input.build_prompt().format_messages()
        assert len(messages) == 4

    def test_style_and_template_adds_both(self):
        seg_input = SegmentationInput(
            script_text="Hello", word_timestamps=[], prompt="System",
            style="cinematic", template_context="vertical",
        )
        messages = seg_input.build_prompt().format_messages()
        assert len(messages) == 5

    def test_word_timestamps_included_in_prompt(self):
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.5),
            WordTimestamp(word="World", start=0.6, end=1.0),
        ]
        seg_input = SegmentationInput(
            script_text="Hello World", word_timestamps=words, prompt="System",
        )
        messages = seg_input.build_prompt().format_messages()
        word_list_content = messages[2].content
        assert "[0]" in word_list_content
        assert "[1]" in word_list_content
        assert "Hello" in word_list_content
        assert "World" in word_list_content


class TestWordTimestampToIndexedStr:
    def test_format_includes_index_and_timing(self):
        word = WordTimestamp(word="Hello", start=0.0, end=0.5)
        result = word.to_indexed_str(0)
        assert "[0]" in result
        assert "Hello" in result
        assert "0.00s" in result
        assert "0.50s" in result

    def test_format_with_higher_index(self):
        word = WordTimestamp(word="World", start=1.25, end=1.75)
        result = word.to_indexed_str(42)
        assert "[42]" in result
        assert "World" in result
