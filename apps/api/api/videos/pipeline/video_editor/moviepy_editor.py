"""MoviePy video editor — renders 9:16 vertical videos with Ken Burns, captions, top text."""

import io
import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

from api.videos.pipeline.tts.schemas import WordTimestamp
from api.videos.pipeline.video_editor.base import VideoEditor
from api.videos.pipeline.video_editor.schemas import (
    AssemblyInput,
    EditResult,
    Segment,
    TextStyle,
    VideoTemplate,
)

logger = logging.getLogger(__name__)


class CaptionGroup(BaseModel):
    """A group of words displayed together as a single subtitle line."""

    text: str
    start: float
    end: float


RENDER_CODEC = "libx264"
RENDER_AUDIO_CODEC = "aac"
RENDER_PRESET = "ultrafast"
RENDER_THREADS = 4


class MoviePyVideoEditor(VideoEditor):
    """Renders videos using MoviePy with Ken Burns effects and text overlays."""

    def assemble_video(self, assembly_input: AssemblyInput) -> EditResult:
        """Assemble final video from assembly input data."""
        template = assembly_input.template
        segments = assembly_input.segments
        audio_bytes = assembly_input.audio_bytes

        logger.info(
            "Assembly starting (%d segments, %d bytes audio)",
            len(segments),
            len(audio_bytes),
        )

        segments = self._align_to_audio(segments, audio_bytes)
        caption_groups = self._group_captions(
            assembly_input.word_timestamps, template.caption_style.max_chars
        )
        caption_font = self._load_font(template.caption_style)
        top_font = (
            self._load_font(template.top_text_style)
            if assembly_input.top_text
            else None
        )

        overlay_cache = self._build_overlay_cache(
            template,
            caption_groups,
            caption_font,
            assembly_input.top_text,
            top_font,
        )

        src_w = int(template.width * template.effect_oversample)
        src_h = int(template.height * template.effect_oversample)

        clips = []
        offset = 0.0
        for segment in segments:
            clips.append(
                self._make_clip(
                    template,
                    segment,
                    offset,
                    src_w,
                    src_h,
                    caption_groups,
                    overlay_cache,
                )
            )
            offset += segment.duration

        result = self._render(clips, audio_bytes, template.fps)
        logger.info(
            "Assembly complete (%dms, %d bytes)",
            result.duration_ms,
            len(result.video_bytes),
        )
        return result

    # ── Audio alignment ─────────────────────────────────────────────

    def _align_to_audio(
        self, segments: list[Segment], audio_bytes: bytes
    ) -> list[Segment]:
        """Extend the last segment to match audio duration."""
        if not segments:
            return segments

        with self._temp_file(".mp3") as audio_path:
            Path(audio_path).write_bytes(audio_bytes)
            clip = AudioFileClip(audio_path)
            audio_duration = clip.duration
            clip.close()

        video_duration = sum(segment.duration for segment in segments)
        gap = audio_duration - video_duration

        if gap <= 0.05:
            return segments

        logger.info(
            "Extending last segment by %.2fs (video=%.2fs, audio=%.2fs)",
            gap,
            video_duration,
            audio_duration,
        )
        last = segments[-1]
        return [
            *segments[:-1],
            Segment(
                image_bytes=last.image_bytes,
                duration=last.duration + gap,
                effect=last.effect,
            ),
        ]

    # ── Caption grouping ─────────────────────────────────────────────

    @staticmethod
    def _group_captions(
        captions: list[WordTimestamp], max_chars: int
    ) -> list[CaptionGroup]:
        """Group words into subtitle chunks limited by max_chars."""
        if not captions:
            return []

        groups: list[CaptionGroup] = []
        current_words: list[str] = []
        current_len = 0
        group_start = captions[0].start

        for caption_word in captions:
            word_len = len(caption_word.word)
            new_len = current_len + word_len + (1 if current_words else 0)

            if new_len > max_chars and current_words:
                groups.append(
                    CaptionGroup(
                        text=" ".join(current_words),
                        start=group_start,
                        end=caption_word.start,
                    )
                )
                current_words = [caption_word.word]
                current_len = word_len
                group_start = caption_word.start
            else:
                current_words.append(caption_word.word)
                current_len = new_len

        if current_words:
            groups.append(
                CaptionGroup(
                    text=" ".join(current_words),
                    start=group_start,
                    end=captions[-1].end,
                )
            )

        return groups

    # ── Font / overlay ───────────────────────────────────────────────

    @staticmethod
    def _load_font(style: TextStyle) -> ImageFont.FreeTypeFont:
        """Load a font from the style config."""
        try:
            return ImageFont.truetype(style.font_path, style.font_size)
        except OSError:
            logger.warning(
                "Font %s not found, falling back to default", style.font_path
            )
            return ImageFont.load_default()

    def _build_overlay_cache(
        self, template, caption_groups, caption_font, top_text, top_font
    ) -> dict:
        """Pre-render all text overlays as RGBA numpy arrays."""
        width, height = template.width, template.height
        cache: dict = {"top": None, "groups": {}}

        if top_text and top_font:
            cache["top"] = self._render_text_overlay(
                width,
                height,
                top_text.upper(),
                top_font,
                template.top_text_style,
            )

        for index, group in enumerate(caption_groups):
            cache["groups"][index] = self._render_text_overlay(
                width,
                height,
                group.text.upper(),
                caption_font,
                template.caption_style,
            )

        return cache

    @staticmethod
    def _render_text_overlay(width, height, text, font, style: TextStyle) -> np.ndarray:
        """Render text into a transparent RGBA overlay array."""
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.text(
            (width // 2, int(height * style.y_position)),
            text,
            font=font,
            fill=style.color,
            stroke_width=style.stroke_width,
            stroke_fill=style.stroke_color,
            anchor="mt",
        )
        return np.array(overlay)

    @staticmethod
    def _composite_overlay(frame: np.ndarray, overlay: np.ndarray) -> np.ndarray:
        """Alpha-composite an RGBA overlay onto an RGB frame."""
        alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0
        rgb = overlay[:, :, :3].astype(np.float32)
        blended = frame.astype(np.float32) * (1 - alpha) + rgb * alpha
        return blended.astype(np.uint8)

    # ── Ken Burns clip ───────────────────────────────────────────────

    def _make_clip(
        self,
        template,
        segment,
        time_offset,
        src_w,
        src_h,
        caption_groups,
        overlay_cache,
    ) -> VideoClip:
        """Create a clip with Ken Burns pan/zoom and pre-rendered text overlays."""
        width, height = template.width, template.height
        src = np.array(
            Image.open(io.BytesIO(segment.image_bytes))
            .convert("RGB")
            .resize((src_w, src_h), Image.BILINEAR)
        )
        source_h, source_w = src.shape[:2]
        direction = segment.effect.direction.value
        scale = segment.effect.scale
        duration = segment.duration
        top_overlay = overlay_cache["top"]
        group_overlays = overlay_cache["groups"]

        def make_frame(local_t: float) -> np.ndarray:
            progress = local_t / duration if duration > 0 else 0.0
            cur_scale, center_x, center_y = _compute_ken_burns(
                direction, scale, progress, source_w, source_h
            )

            crop_w = int(source_w / cur_scale)
            crop_h = int(source_h / cur_scale)
            x_start = max(0, center_x - crop_w // 2)
            y_start = max(0, center_y - crop_h // 2)

            cropped = src[y_start : y_start + crop_h, x_start : x_start + crop_w]
            frame = np.array(
                Image.fromarray(cropped).resize((width, height), Image.BILINEAR)
            )

            if top_overlay is not None:
                frame = self._composite_overlay(frame, top_overlay)

            global_t = time_offset + local_t
            for group_index, group in enumerate(caption_groups):
                if group.start <= global_t < group.end:
                    frame = self._composite_overlay(frame, group_overlays[group_index])
                    break

            return frame

        return VideoClip(frame_function=make_frame, duration=duration).with_fps(
            template.fps
        )

    # ── Render ───────────────────────────────────────────────────────

    def _render(
        self, clips: list[VideoClip], audio_bytes: bytes, fps: int
    ) -> EditResult:
        """Concatenate clips, attach audio, and render to MP4."""
        video_clip = audio_clip = None

        with (
            self._temp_file(".mp3") as audio_path,
            self._temp_file(".mp4") as output_path,
        ):
            Path(audio_path).write_bytes(audio_bytes)

            try:
                video_clip = concatenate_videoclips(clips, method="compose")
                audio_clip = AudioFileClip(audio_path)
                video_clip = video_clip.with_audio(audio_clip)

                video_clip.write_videofile(
                    output_path,
                    fps=fps,
                    codec=RENDER_CODEC,
                    audio_codec=RENDER_AUDIO_CODEC,
                    preset=RENDER_PRESET,
                    threads=RENDER_THREADS,
                    logger="bar",
                )

                return EditResult(
                    video_bytes=Path(output_path).read_bytes(),
                    duration_ms=int(video_clip.duration * 1000),
                )
            finally:
                if video_clip:
                    video_clip.close()
                if audio_clip:
                    audio_clip.close()

    @staticmethod
    @contextmanager
    def _temp_file(suffix: str):
        """Yield a temp file path that's cleaned up on exit."""
        path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                path = temp_file.name
            yield path
        finally:
            if path:
                Path(path).unlink(missing_ok=True)


def _compute_ken_burns(
    direction: str,
    scale: float,
    progress: float,
    width: int,
    height: int,
) -> tuple[float, int, int]:
    """Return (current_scale, center_x, center_y) for a Ken Burns frame."""
    center_x, center_y = width // 2, height // 2

    if direction == "zoom_in":
        cur_scale = 1.0 + (scale - 1.0) * progress
    elif direction == "zoom_out":
        cur_scale = scale - (scale - 1.0) * progress
    else:
        cur_scale = scale

    crop_w = int(width / cur_scale)
    crop_h = int(height / cur_scale)
    pan_offset_x = (width - crop_w) // 2
    pan_offset_y = (height - crop_h) // 2

    if direction == "pan_left":
        center_x += int(pan_offset_x * (1 - progress))
    elif direction == "pan_right":
        center_x -= int(pan_offset_x * (1 - progress))
    elif direction == "pan_up":
        center_y += int(pan_offset_y * (1 - progress))
    elif direction == "pan_down":
        center_y -= int(pan_offset_y * (1 - progress))

    return cur_scale, center_x, center_y
