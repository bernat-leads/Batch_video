"""Video editor schemas and template configuration."""

import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

from api.settings import settings
from api.videos.pipeline.image_generation.schemas import ImageConfig
from api.videos.pipeline.segmentation.schemas import AnySegmentEffect
from api.videos.pipeline.tts.schemas import WordTimestamp

logger = logging.getLogger(__name__)

BUNDLED_FONT = str(Path(settings.FONT_DIR) / "Montserrat-Bold.ttf")


class TextStyle(BaseModel):
    """Style config for a text overlay (captions, top text)."""

    font_path: str = BUNDLED_FONT
    font_size: int = 72
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 4
    y_position: float = 0.5
    max_chars: int = 30

    def load_font(self) -> ImageFont.FreeTypeFont:
        """Load the configured font, falling back to PIL default."""
        try:
            return ImageFont.truetype(self.font_path, self.font_size)
        except OSError:
            logger.warning("Font %s not found, falling back to default", self.font_path)
            return ImageFont.load_default()

    def render_overlay(self, width: int, height: int, text: str) -> np.ndarray:
        """Render text into a transparent RGBA overlay array using this style."""
        font = self.load_font()
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.text(
            (width // 2, int(height * self.y_position)),
            text,
            font=font,
            fill=self.color,
            stroke_width=self.stroke_width,
            stroke_fill=self.stroke_color,
            anchor="mt",
        )
        return np.array(overlay)


class VideoTemplate(BaseModel):
    """Pure data class holding all template configuration.

    Used by pipeline steps (segmentation, image gen) and the video editor.
    Different templates (TikTok, YouTube Shorts, etc.) are just different instances.
    """

    width: int = 1080
    height: int = 1920
    fps: int = 30
    effect_oversample: float = 1.5
    image_config: ImageConfig = ImageConfig()
    caption_style: TextStyle = TextStyle()
    top_text_style: TextStyle = TextStyle()
    template_context: str = ""


class Segment(BaseModel):
    """A single visual segment with image, timing, and visual effect.

    Built from Shot records after downloading images from S3.
    Input to VideoEditor.assemble_video().
    """

    image_bytes: bytes
    duration: float
    effect: AnySegmentEffect


class CaptionGroup(BaseModel):
    """A group of words displayed together as a single subtitle line."""

    text: str
    start: float
    end: float

    @classmethod
    def from_word_timestamps(
        cls, words: list[WordTimestamp], max_chars: int
    ) -> list["CaptionGroup"]:
        """Group words into subtitle chunks limited by max_chars."""
        if not words:
            return []

        groups: list[CaptionGroup] = []
        current_words: list[str] = []
        current_len = 0
        group_start = words[0].start

        for word in words:
            word_len = len(word.word)
            new_len = current_len + word_len + (1 if current_words else 0)

            if new_len > max_chars and current_words:
                groups.append(
                    cls(
                        text=" ".join(current_words),
                        start=group_start,
                        end=word.start,
                    )
                )
                current_words = [word.word]
                current_len = word_len
                group_start = word.start
            else:
                current_words.append(word.word)
                current_len = new_len

        if current_words:
            groups.append(
                cls(
                    text=" ".join(current_words),
                    start=group_start,
                    end=words[-1].end,
                )
            )

        return groups


class OverlayCache(BaseModel):
    """Pre-rendered RGBA text overlays for compositing onto frames."""

    model_config = {"arbitrary_types_allowed": True}

    top_overlay: np.ndarray | None = None
    caption_overlays: dict[int, np.ndarray] = {}

    @classmethod
    def build(
        cls,
        template: VideoTemplate,
        caption_groups: list[CaptionGroup],
        top_text: str | None,
    ) -> "OverlayCache":
        """Pre-render all text overlays from template styles."""
        width, height = template.width, template.height

        top_overlay = (
            template.top_text_style.render_overlay(width, height, top_text.upper())
            if top_text
            else None
        )

        caption_overlays = {
            index: template.caption_style.render_overlay(
                width, height, group.text.upper()
            )
            for index, group in enumerate(caption_groups)
        }

        return cls(top_overlay=top_overlay, caption_overlays=caption_overlays)


class AssemblyInput(BaseModel):
    """Everything the video editor needs to assemble a video.

    Built by VideoService from shots, TTS output, and video metadata.
    Decouples the editor from the database model.
    """

    template: VideoTemplate
    segments: list[Segment]
    audio_bytes: bytes
    word_timestamps: list[WordTimestamp]
    top_text: str | None = None


class EditResult(BaseModel):
    """Output of the video editor."""

    video_bytes: bytes
    duration_ms: int

    model_config = {"frozen": True}
