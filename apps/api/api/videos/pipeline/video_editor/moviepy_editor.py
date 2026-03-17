"""MoviePy video editor — renders 9:16 vertical videos with Ken Burns, captions, top text."""

import logging
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips

from api.videos.utils import fast_composite, temp_file
from api.videos.pipeline.video_editor.base import VideoEditor
from api.videos.pipeline.video_editor.effects import EffectService
from api.videos.pipeline.video_editor.schemas import (
    CAPTION_SLIDE_DISTANCE,
    CAPTION_SLIDE_DURATION,
    AssemblyInput,
    CaptionGroup,
    EditResult,
    OverlayCache,
    Segment,
    VideoTemplate,
)

logger = logging.getLogger(__name__)

RENDER_CODEC = "libx264"
RENDER_AUDIO_CODEC = "aac"
RENDER_PRESET = "fast"
RENDER_THREADS = 8
AUDIO_SYNC_TOLERANCE = 0.05


class MoviePyVideoEditor(VideoEditor):
    """Renders videos using MoviePy with Ken Burns effects and text overlays."""

    def __init__(self, effects: EffectService) -> None:
        self._effects = effects

    def assemble_video(self, assembly_input: AssemblyInput) -> EditResult:
        """Assemble final video from assembly input data."""
        template = assembly_input.template
        logger.info(
            "Assembly starting (%d segments, %d bytes audio)",
            len(assembly_input.segments),
            len(assembly_input.audio_bytes),
        )

        segments = self._align_segments_to_audio(
            assembly_input.segments, assembly_input.audio_bytes
        )
        caption_groups = CaptionGroup.from_word_timestamps(
            assembly_input.word_timestamps,
            max_chars=template.caption_style.max_chars,
            max_words=template.caption_style.max_words,
        )
        for i, group in enumerate(caption_groups):
            logger.debug(
                "Caption[%d] %.2fs-%.2fs: %s", i, group.start, group.end, group.text
            )

        overlays = OverlayCache.build(template, caption_groups, assembly_input.top_text)
        clips = self._build_clips(template, segments, caption_groups, overlays)
        result = self._render_to_mp4(clips, assembly_input.audio_bytes, template.fps)

        logger.info(
            "Assembly complete (%dms, %d bytes)",
            result.duration_ms,
            len(result.video_bytes),
        )
        return result

    # ── Align segments to audio ───────────────────────────────────────

    def _align_segments_to_audio(
        self, segments: list[Segment], audio_bytes: bytes
    ) -> list[Segment]:
        """Extend the last segment so total video duration matches audio."""
        if not segments:
            return segments

        with temp_file(".mp3") as audio_path:
            Path(audio_path).write_bytes(audio_bytes)
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            audio_clip.close()

        video_duration = sum(segment.duration for segment in segments)
        gap = audio_duration - video_duration

        if gap <= AUDIO_SYNC_TOLERANCE:
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

    # ── Build clips ───────────────────────────────────────────────────

    def _build_clips(
        self,
        template: VideoTemplate,
        segments: list[Segment],
        caption_groups: list[CaptionGroup],
        overlays: OverlayCache,
    ) -> list[VideoClip]:
        """Create a MoviePy clip per segment."""
        output_size = (template.width, template.height)
        source_size = (
            int(template.width * template.effect_oversample),
            int(template.height * template.effect_oversample),
        )

        clips: list[VideoClip] = []
        time_offset = 0.0
        for segment in segments:
            clip = self._make_segment_clip(
                segment,
                time_offset,
                source_size,
                output_size,
                caption_groups,
                overlays,
                template.fps,
            )
            clips.append(clip)
            time_offset += segment.duration
        return clips

    def _make_segment_clip(
        self,
        segment: Segment,
        time_offset: float,
        source_size: tuple[int, int],
        output_size: tuple[int, int],
        caption_groups: list[CaptionGroup],
        overlays: OverlayCache,
        fps: int,
    ) -> VideoClip:
        """Create a single clip with effect + animated text overlays."""
        source_image = self._decode_image(segment.image_bytes, source_size)
        effect = segment.effect
        duration = segment.duration
        output_width, output_height = output_size

        def make_frame(local_time: float) -> np.ndarray:
            progress = local_time / duration if duration > 0 else 0.0
            frame = self._effects.apply(
                effect, source_image, progress, output_width, output_height
            )
            frame = self._composite_overlays(
                frame, overlays, caption_groups, time_offset + local_time
            )
            return frame

        return VideoClip(frame_function=make_frame, duration=duration).with_fps(fps)

    # ── Frame compositing ─────────────────────────────────────────────

    @staticmethod
    def _composite_overlays(
        frame: np.ndarray,
        overlays: OverlayCache,
        caption_groups: list[CaptionGroup],
        global_time: float,
    ) -> np.ndarray:
        """Composite top text and animated caption onto a frame."""
        if overlays.top is not None:
            frame = fast_composite(
                frame, overlays.top.inv_alpha, overlays.top.premultiplied_rgb
            )

        for group_index, group in enumerate(caption_groups):
            if group.start <= global_time < group.end:
                overlay = overlays.captions[group_index]
                time_into_group = global_time - group.start

                if time_into_group < CAPTION_SLIDE_DURATION:
                    anim_progress = time_into_group / CAPTION_SLIDE_DURATION
                    eased = 1.0 - (1.0 - anim_progress) ** 3
                    offset_y = int(CAPTION_SLIDE_DISTANCE * (1.0 - eased))
                    inv_alpha, premultiplied_rgb = overlay.shifted(offset_y)
                    frame = fast_composite(frame, inv_alpha, premultiplied_rgb)
                else:
                    frame = fast_composite(
                        frame, overlay.inv_alpha, overlay.premultiplied_rgb
                    )
                break

        return frame

    # ── Image decoding ────────────────────────────────────────────────

    @staticmethod
    def _decode_image(image_bytes: bytes, target_size: tuple[int, int]) -> np.ndarray:
        """Decode image bytes and resize to target dimensions using cv2."""
        raw = np.frombuffer(image_bytes, dtype=np.uint8)
        decoded = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        resized = cv2.resize(decoded, target_size, interpolation=cv2.INTER_LINEAR)
        return cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    # ── Render to MP4 ─────────────────────────────────────────────────

    def _render_to_mp4(
        self, clips: list[VideoClip], audio_bytes: bytes, fps: int
    ) -> EditResult:
        """Concatenate clips, attach audio, and render to MP4 bytes."""
        video_clip = audio_clip = None

        with temp_file(".mp3") as audio_path, temp_file(".mp4") as output_path:
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
                    ffmpeg_params=["-crf", "28"],
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
