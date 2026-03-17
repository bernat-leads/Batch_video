"""MoviePy video editor — renders 9:16 vertical videos with Ken Burns, captions, top text."""

import io
import logging
from pathlib import Path

import numpy as np
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips
from PIL import Image

from api.videos.utils import composite_overlay, temp_file
from api.videos.pipeline.video_editor.base import VideoEditor
from api.videos.pipeline.video_editor.schemas import (
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
RENDER_PRESET = "ultrafast"
RENDER_THREADS = 4
AUDIO_SYNC_TOLERANCE = 0.05  # seconds


class MoviePyVideoEditor(VideoEditor):
    """Renders videos using MoviePy with Ken Burns effects and text overlays.

    Pipeline:
    1. Align segment durations to audio length
    2. Group word timestamps into caption chunks
    3. Pre-render all text overlays (top text + captions)
    4. Build a MoviePy clip per segment (Ken Burns + overlay compositing)
    5. Concatenate clips, attach audio, render to MP4
    """

    def assemble_video(self, assembly_input: AssemblyInput) -> EditResult:
        """Assemble final video from assembly input data."""
        template = assembly_input.template

        logger.info(
            "Assembly starting (%d segments, %d bytes audio)",
            len(assembly_input.segments),
            len(assembly_input.audio_bytes),
        )

        segments = self._align_segments_to_audio(assembly_input.segments, assembly_input.audio_bytes)
        caption_groups = CaptionGroup.from_word_timestamps(
            assembly_input.word_timestamps, template.caption_style.max_chars,
        )
        overlays = OverlayCache.build(template, caption_groups, assembly_input.top_text)
        clips = self._build_clips(template, segments, caption_groups, overlays)
        result = self._render_to_mp4(clips, assembly_input.audio_bytes, template.fps)

        logger.info("Assembly complete (%dms, %d bytes)", result.duration_ms, len(result.video_bytes))
        return result

    # ── Step 1: Align segments ────────────────────────────────────────

    def _align_segments_to_audio(self, segments: list[Segment], audio_bytes: bytes) -> list[Segment]:
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

        logger.info("Extending last segment by %.2fs (video=%.2fs, audio=%.2fs)", gap, video_duration, audio_duration)
        last = segments[-1]
        return [
            *segments[:-1],
            Segment(image_bytes=last.image_bytes, duration=last.duration + gap, effect=last.effect),
        ]

    # ── Step 2: Build clips ───────────────────────────────────────────

    def _build_clips(
        self,
        template: VideoTemplate,
        segments: list[Segment],
        caption_groups: list[CaptionGroup],
        overlays: OverlayCache,
    ) -> list[VideoClip]:
        """Create a MoviePy clip for each segment with Ken Burns + text overlays."""
        output_width, output_height = template.width, template.height
        source_width = int(output_width * template.effect_oversample)
        source_height = int(output_height * template.effect_oversample)

        clips: list[VideoClip] = []
        time_offset = 0.0

        for segment in segments:
            clip = self._make_segment_clip(
                segment, time_offset,
                source_width, source_height,
                output_width, output_height,
                caption_groups, overlays, template.fps,
            )
            clips.append(clip)
            time_offset += segment.duration

        return clips

    def _make_segment_clip(
        self,
        segment: Segment,
        time_offset: float,
        source_width: int,
        source_height: int,
        output_width: int,
        output_height: int,
        caption_groups: list[CaptionGroup],
        overlays: OverlayCache,
        fps: int,
    ) -> VideoClip:
        """Create a single clip with effect animation and composited text overlays."""
        source_image = np.array(
            Image.open(io.BytesIO(segment.image_bytes))
            .convert("RGB")
            .resize((source_width, source_height), Image.BILINEAR)
        )
        effect = segment.effect
        duration = segment.duration

        def make_frame(local_time: float) -> np.ndarray:
            progress = local_time / duration if duration > 0 else 0.0
            frame = effect.apply_frame(source_image, progress, output_width, output_height)

            if overlays.top_overlay is not None:
                frame = composite_overlay(frame, overlays.top_overlay)

            global_time = time_offset + local_time
            for group_index, group in enumerate(caption_groups):
                if group.start <= global_time < group.end:
                    frame = composite_overlay(frame, overlays.caption_overlays[group_index])
                    break

            return frame

        return VideoClip(frame_function=make_frame, duration=duration).with_fps(fps)

    # ── Step 3: Render to MP4 ─────────────────────────────────────────

    def _render_to_mp4(self, clips: list[VideoClip], audio_bytes: bytes, fps: int) -> EditResult:
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
