"""MoviePy TikTok ad video template — 9:16 vertical with Ken Burns, captions, top text."""

import io
import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

from api.settings import settings
from api.videos.pipeline.config import FPS, HEIGHT, KEN_BURNS_OVERSAMPLE, WIDTH
from api.videos.pipeline.video_editor.base import VideoTemplate
from api.videos.pipeline.video_editor.schemas import CaptionWord, EditResult, Segment

logger = logging.getLogger(__name__)

# ── Template config ──────────────────────────────────────────────────
FONT_PATH = settings.CAPTION_FONT_PATH
RENDER_CODEC = "libx264"
RENDER_AUDIO_CODEC = "aac"
RENDER_PRESET = "medium"
RENDER_THREADS = 2

# Captions (subtitles at bottom)
CAPTION_FONT_SIZE = 72
CAPTION_COLOR = "white"
CAPTION_STROKE_COLOR = "black"
CAPTION_STROKE_WIDTH = 3
CAPTION_Y_POSITION = 0.75  # fraction of HEIGHT
CAPTION_MAX_CHARS = 30  # max characters per subtitle group

# Top text (persistent headline near top)
TOP_TEXT_FONT_SIZE = 56
TOP_TEXT_COLOR = "white"
TOP_TEXT_STROKE_COLOR = "black"
TOP_TEXT_STROKE_WIDTH = 3
TOP_TEXT_Y_POSITION = 0.10  # fraction of HEIGHT


class MoviePyTikTokAdTemplate(VideoTemplate):
    """9:16 vertical TikTok ad with Ken Burns effects, assembled via MoviePy."""

    _SRC_W = int(WIDTH * KEN_BURNS_OVERSAMPLE)
    _SRC_H = int(HEIGHT * KEN_BURNS_OVERSAMPLE)

    def assemble_video(
        self,
        segments: list[Segment],
        audio_bytes: bytes,
        captions: list[CaptionWord],
        top_text: str | None = None,
    ) -> EditResult:
        logger.info(
            "Assembly starting (%d segments, %d captions, %d bytes audio)",
            len(segments),
            len(captions),
            len(audio_bytes),
        )

        # Extend the last segment so the video covers the full audio duration.
        # The LLM-generated segment boundaries may end before the final word's
        # trailing silence, causing the video to be shorter than the audio.
        segments = self._align_to_audio(segments, audio_bytes)

        caption_groups = self._group_captions(captions)
        caption_font = self._load_font(CAPTION_FONT_SIZE)
        top_font = self._load_font(TOP_TEXT_FONT_SIZE) if top_text else None

        clips = []
        offset = 0.0
        for seg in segments:
            clips.append(
                self._make_clip(
                    seg, offset, caption_groups, caption_font, top_text, top_font
                )
            )
            offset += seg.duration

        result = self._render(clips, audio_bytes)
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
        """Extend the last segment so total video duration matches the audio.

        If the audio is longer than the sum of segment durations, the last
        segment's duration is increased to cover the gap. This prevents the
        video track from being shorter than the audio track.
        """
        if not segments:
            return segments

        with self._temp_file(".mp3") as audio_path:
            Path(audio_path).write_bytes(audio_bytes)
            clip = AudioFileClip(audio_path)
            audio_duration = clip.duration
            clip.close()

        video_duration = sum(seg.duration for seg in segments)
        gap = audio_duration - video_duration

        if gap <= 0.05:  # within a frame — no adjustment needed
            return segments

        logger.info(
            "Extending last segment by %.2fs to match audio (video=%.2fs, audio=%.2fs)",
            gap,
            video_duration,
            audio_duration,
        )

        # Rebuild list with extended last segment
        last = segments[-1]
        extended_last = Segment(
            image_bytes=last.image_bytes,
            duration=last.duration + gap,
            ken_burns=last.ken_burns,
        )
        return [*segments[:-1], extended_last]

    # ── Caption grouping ─────────────────────────────────────────────

    @staticmethod
    def _group_captions(captions: list[CaptionWord]) -> list[dict]:
        """Group words into subtitle chunks limited by CAPTION_MAX_CHARS."""
        if not captions:
            return []

        groups: list[dict] = []
        current_words: list[str] = []
        current_len = 0
        group_start = captions[0].start

        for cw in captions:
            word_len = len(cw.word)
            new_len = current_len + word_len + (1 if current_words else 0)

            if new_len > CAPTION_MAX_CHARS and current_words:
                groups.append(
                    {
                        "text": " ".join(current_words),
                        "start": group_start,
                        "end": cw.start,
                    }
                )
                current_words = [cw.word]
                current_len = word_len
                group_start = cw.start
            else:
                current_words.append(cw.word)
                current_len = new_len

        if current_words:
            groups.append(
                {
                    "text": " ".join(current_words),
                    "start": group_start,
                    "end": captions[-1].end,
                }
            )

        return groups

    # ── Font ─────────────────────────────────────────────────────────

    @staticmethod
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except OSError:
            logger.warning("Font %s not found, falling back to default", FONT_PATH)
            return ImageFont.load_default()

    # ── Text rendering ───────────────────────────────────────────────

    @staticmethod
    def _draw_stroked_text(
        draw: ImageDraw.ImageDraw,
        xy: tuple[float, float],
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: str,
        stroke_fill: str,
        stroke_width: int,
    ) -> None:
        draw.text(
            xy,
            text,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
            anchor="mt",
        )

    def _burn_overlays(
        self,
        frame: np.ndarray,
        global_t: float,
        caption_groups: list[dict],
        caption_font: ImageFont.FreeTypeFont,
        top_text: str | None,
        top_font: ImageFont.FreeTypeFont | None,
    ) -> np.ndarray:
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img)

        # Top text — always visible
        if top_text and top_font:
            self._draw_stroked_text(
                draw,
                (WIDTH // 2, int(HEIGHT * TOP_TEXT_Y_POSITION)),
                top_text.upper(),
                top_font,
                TOP_TEXT_COLOR,
                TOP_TEXT_STROKE_COLOR,
                TOP_TEXT_STROKE_WIDTH,
            )

        # Captions — show active group
        for group in caption_groups:
            if group["start"] <= global_t < group["end"]:
                self._draw_stroked_text(
                    draw,
                    (WIDTH // 2, int(HEIGHT * CAPTION_Y_POSITION)),
                    group["text"].upper(),
                    caption_font,
                    CAPTION_COLOR,
                    CAPTION_STROKE_COLOR,
                    CAPTION_STROKE_WIDTH,
                )
                break

        return np.array(img)

    # ── Ken Burns clip ───────────────────────────────────────────────

    def _make_clip(
        self,
        segment: Segment,
        time_offset: float,
        caption_groups: list[dict],
        caption_font: ImageFont.FreeTypeFont,
        top_text: str | None,
        top_font: ImageFont.FreeTypeFont | None,
    ) -> VideoClip:
        src = np.array(
            Image.open(io.BytesIO(segment.image_bytes))
            .convert("RGB")
            .resize((self._SRC_W, self._SRC_H), Image.LANCZOS)
        )
        h, w = src.shape[:2]
        direction = segment.ken_burns.direction.value
        scale = segment.ken_burns.scale
        dur = segment.duration

        def make_frame(t: float) -> np.ndarray:
            progress = t / dur if dur > 0 else 0.0
            cur_scale, cx, cy = self._compute_ken_burns(
                direction, scale, progress, w, h
            )

            crop_w, crop_h = int(w / cur_scale), int(h / cur_scale)
            x1 = max(0, cx - crop_w // 2)
            y1 = max(0, cy - crop_h // 2)

            cropped = Image.fromarray(src[y1 : y1 + crop_h, x1 : x1 + crop_w])
            frame = np.array(cropped.resize((WIDTH, HEIGHT), Image.LANCZOS))

            return self._burn_overlays(
                frame,
                time_offset + t,
                caption_groups,
                caption_font,
                top_text,
                top_font,
            )

        return VideoClip(frame_function=make_frame, duration=dur).with_fps(FPS)

    # ── Render ───────────────────────────────────────────────────────

    def _render(self, clips: list[VideoClip], audio_bytes: bytes) -> EditResult:
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
                    fps=FPS,
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

    # ── Ken Burns math ───────────────────────────────────────────────

    @staticmethod
    def _compute_ken_burns(
        direction: str,
        scale: float,
        progress: float,
        w: int,
        h: int,
    ) -> tuple[float, int, int]:
        cx, cy = w // 2, h // 2

        if direction == "zoom_in":
            cur_scale = 1.0 + (scale - 1.0) * progress
        elif direction == "zoom_out":
            cur_scale = scale - (scale - 1.0) * progress
        else:
            cur_scale = scale

        crop_w, crop_h = int(w / cur_scale), int(h / cur_scale)
        pan_offset_x = (w - crop_w) // 2
        pan_offset_y = (h - crop_h) // 2

        if direction == "pan_left":
            cx += int(pan_offset_x * (1 - progress))
        elif direction == "pan_right":
            cx -= int(pan_offset_x * (1 - progress))
        elif direction == "pan_up":
            cy += int(pan_offset_y * (1 - progress))
        elif direction == "pan_down":
            cy -= int(pan_offset_y * (1 - progress))

        return cur_scale, cx, cy

    @staticmethod
    @contextmanager
    def _temp_file(suffix: str):
        path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                path = f.name
            yield path
        finally:
            if path:
                Path(path).unlink(missing_ok=True)
