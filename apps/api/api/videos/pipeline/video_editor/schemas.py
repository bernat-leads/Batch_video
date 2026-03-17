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

BUNDLED_FONT = str(Path(settings.FONT_DIR) / "Montserrat-Black.ttf")


class TextStyle(BaseModel):
    """Style config for a text overlay (captions, top text)."""

    font_path: str = BUNDLED_FONT
    font_size: int = 72
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 4
    y_position: float = 0.5
    max_chars: int = 30
    max_words: int = 5

    def load_font(self) -> ImageFont.FreeTypeFont:
        """Load the configured font, falling back to PIL default."""
        try:
            return ImageFont.truetype(self.font_path, self.font_size)
        except OSError:
            logger.warning("Font %s not found, falling back to default", self.font_path)
            return ImageFont.load_default()

    def render_overlay(self, width: int, height: int, text: str) -> np.ndarray:
        """Render text into a transparent RGBA overlay, wrapping if too wide.

        Wraps text into multiple centered lines if it exceeds 90% of frame width.
        Each line is centered horizontally, stacked vertically from y_position.
        """
        font = self.load_font()
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        max_width = int(width * 0.9)

        lines = self._wrap_text(draw, text, font, max_width)
        line_height = draw.textbbox(
            (0, 0), "Ay", font=font, stroke_width=self.stroke_width
        )[3]
        total_height = line_height * len(lines)
        start_y = int(height * self.y_position) - total_height // 2

        for line_index, line in enumerate(lines):
            bbox = draw.textbbox(
                (0, 0), line, font=font, stroke_width=self.stroke_width
            )
            line_width = bbox[2] - bbox[0]
            line_x = (width - line_width) // 2
            line_y = start_y + line_index * line_height
            draw.text(
                (line_x, line_y),
                line,
                font=font,
                fill=self.color,
                stroke_width=self.stroke_width,
                stroke_fill=self.stroke_color,
            )

        return np.array(overlay)

    @staticmethod
    def _wrap_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> list[str]:
        """Split text into lines that fit within max_width pixels."""
        words = text.split()
        if not words:
            return [text]

        lines: list[str] = []
        current_line: list[str] = []

        for word in words:
            test_line = " ".join([*current_line, word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines


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
        cls, words: list[WordTimestamp], max_chars: int, max_words: int = 3
    ) -> list["CaptionGroup"]:
        """Group words into TikTok-style caption chunks.

        Each group is limited by both max_chars and max_words,
        producing short punchy captions (1-3 words) that pop on screen.
        """
        if not words:
            return []

        groups: list[CaptionGroup] = []
        current_words: list[str] = []
        current_len = 0
        group_start = words[0].start

        for word in words:
            word_len = len(word.word)
            new_len = current_len + word_len + (1 if current_words else 0)
            word_count = len(current_words) + 1

            if (new_len > max_chars or word_count > max_words) and current_words:
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


CAPTION_SLIDE_DURATION = 0.15  # seconds for slide-up animation
CAPTION_SLIDE_DISTANCE = 80  # pixels to slide up from


class PrecomputedOverlay(BaseModel):
    """Pre-computed overlay data for fast per-frame compositing."""

    model_config = {"arbitrary_types_allowed": True}

    inv_alpha: np.ndarray
    premultiplied_rgb: np.ndarray

    def shifted(self, offset_y: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (inv_alpha, premultiplied_rgb) shifted down by offset_y pixels.

        Positive offset_y shifts the overlay downward. Used for slide-up animation.
        """
        if offset_y == 0:
            return self.inv_alpha, self.premultiplied_rgb

        height = self.inv_alpha.shape[0]
        ones = np.ones_like(self.inv_alpha[:1])
        zeros = np.zeros_like(self.premultiplied_rgb[:1])

        if offset_y > 0:
            shifted_inv = np.concatenate(
                [
                    np.broadcast_to(ones, (offset_y, *ones.shape[1:])),
                    self.inv_alpha[: height - offset_y],
                ],
                axis=0,
            )
            shifted_rgb = np.concatenate(
                [
                    np.broadcast_to(zeros, (offset_y, *zeros.shape[1:])),
                    self.premultiplied_rgb[: height - offset_y],
                ],
                axis=0,
            )
        else:
            abs_offset = abs(offset_y)
            shifted_inv = np.concatenate(
                [
                    self.inv_alpha[abs_offset:],
                    np.broadcast_to(ones, (abs_offset, *ones.shape[1:])),
                ],
                axis=0,
            )
            shifted_rgb = np.concatenate(
                [
                    self.premultiplied_rgb[abs_offset:],
                    np.broadcast_to(zeros, (abs_offset, *zeros.shape[1:])),
                ],
                axis=0,
            )

        return shifted_inv, shifted_rgb


class OverlayCache(BaseModel):
    """Pre-rendered and pre-computed text overlays for fast frame compositing."""

    model_config = {"arbitrary_types_allowed": True}

    top: PrecomputedOverlay | None = None
    captions: dict[int, PrecomputedOverlay] = {}

    @classmethod
    def build(
        cls,
        template: VideoTemplate,
        caption_groups: list[CaptionGroup],
        top_text: str | None,
    ) -> "OverlayCache":
        """Pre-render all text overlays and pre-compute alpha channels."""
        from api.videos.utils import precompute_overlay

        width, height = template.width, template.height

        top = None
        if top_text:
            rgba = template.top_text_style.render_overlay(
                width, height, top_text.upper()
            )
            _, inv_alpha, premultiplied_rgb = precompute_overlay(rgba)
            top = PrecomputedOverlay(
                inv_alpha=inv_alpha, premultiplied_rgb=premultiplied_rgb
            )

        captions: dict[int, PrecomputedOverlay] = {}
        for index, group in enumerate(caption_groups):
            rgba = template.caption_style.render_overlay(
                width, height, group.text.upper()
            )
            _, inv_alpha, premultiplied_rgb = precompute_overlay(rgba)
            captions[index] = PrecomputedOverlay(
                inv_alpha=inv_alpha, premultiplied_rgb=premultiplied_rgb
            )

        return cls(top=top, captions=captions)


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
