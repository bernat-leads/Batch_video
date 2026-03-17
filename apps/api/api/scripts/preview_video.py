"""Generate a preview video with placeholder frames for testing text overlays.

Usage:
    poetry run preview-video
    poetry run preview-video --output /tmp/test.mp4
    poetry run preview-video --top-text "50% OFF TODAY"
    poetry run preview-video --segments 3 --duration 4
"""

import argparse
import io
import logging
from pathlib import Path

from PIL import Image, ImageDraw

from api.videos.pipeline.segmentation.schemas import KenBurnsDirection, KenBurnsEffect
from api.videos.pipeline.tts.schemas import WordTimestamp
from api.videos.pipeline.video_editor.moviepy_editor import MoviePyVideoEditor
from api.videos.pipeline.video_editor.schemas import AssemblyInput, Segment
from api.videos.pipeline.video_editor.templates import TIKTOK_AD_TEMPLATE

logging.basicConfig(level=logging.INFO)

SEGMENT_COLORS = [
    (45, 55, 72),
    (56, 42, 68),
    (42, 63, 56),
    (68, 51, 42),
    (52, 52, 68),
    (63, 42, 52),
]

SAMPLE_SCRIPT = (
    "Transform your morning routine with our new organic coffee blend. "
    "Sourced from the finest farms in Colombia. "
    "Rich, bold flavor that wakes you up naturally. "
    "Order now and get free shipping on your first bag."
)


def _make_placeholder_image(
    width: int, height: int, color: tuple[int, int, int], label: str
) -> bytes:
    """Create a colored placeholder image with a centered label."""
    image = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(image)
    draw.text(
        (width // 2, height // 2),
        label,
        fill=(255, 255, 255, 128),
        anchor="mm",
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _make_silent_wav(duration_seconds: float, sample_rate: int = 22050) -> bytes:
    """Generate silent WAV audio bytes for the given duration."""
    import struct

    num_samples = int(sample_rate * duration_seconds)
    data_size = num_samples * 2

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return header + b"\x00" * data_size


def _distribute_words(
    script: str, num_segments: int, segment_duration: float
) -> list[WordTimestamp]:
    """Split script into words with evenly distributed fake timing."""
    words = script.split()
    total_duration = num_segments * segment_duration
    word_duration = total_duration / len(words)
    return [
        WordTimestamp(
            word=word,
            start=round(index * word_duration, 3),
            end=round((index + 1) * word_duration, 3),
        )
        for index, word in enumerate(words)
    ]


def generate_preview(
    output_path: str = "preview.mp4",
    num_segments: int = 4,
    segment_duration: float = 5.0,
    top_text: str | None = "LIMITED OFFER",
    script: str = SAMPLE_SCRIPT,
) -> Path:
    """Generate a preview video with placeholder frames and return the output path."""
    template = TIKTOK_AD_TEMPLATE
    src_width = int(template.width * template.effect_oversample)
    src_height = int(template.height * template.effect_oversample)

    directions = list(KenBurnsDirection)
    all_timestamps = _distribute_words(script, num_segments, segment_duration)

    segments = [
        Segment(
            image_bytes=_make_placeholder_image(
                src_width, src_height,
                SEGMENT_COLORS[index % len(SEGMENT_COLORS)],
                f"Shot {index + 1}",
            ),
            duration=segment_duration,
            effect=KenBurnsEffect(
                direction=directions[index % len(directions)],
                scale=1.2,
            ),
        )
        for index in range(num_segments)
    ]

    assembly_input = AssemblyInput(
        template=template,
        segments=segments,
        audio_bytes=_make_silent_wav(num_segments * segment_duration),
        word_timestamps=all_timestamps,
        top_text=top_text,
    )

    editor = MoviePyVideoEditor()
    result = editor.assemble_video(assembly_input)

    path = Path(output_path)
    path.write_bytes(result.video_bytes)
    print(f"Preview video saved to {path.resolve()} ({result.duration_ms}ms)")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a preview video for testing text overlays")
    parser.add_argument("--output", default="preview.mp4", help="Output file path")
    parser.add_argument("--segments", type=int, default=4, help="Number of segments")
    parser.add_argument("--duration", type=float, default=5.0, help="Duration per segment (seconds)")
    parser.add_argument("--top-text", default="LIMITED OFFER", help="Top text overlay (empty to disable)")
    parser.add_argument("--script", default=SAMPLE_SCRIPT, help="Script text for captions")
    args = parser.parse_args()

    generate_preview(
        output_path=args.output,
        num_segments=args.segments,
        segment_duration=args.duration,
        top_text=args.top_text or None,
        script=args.script,
    )


if __name__ == "__main__":
    main()
