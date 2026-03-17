"""Video editor schemas and template configuration."""

from pathlib import Path

from pydantic import BaseModel

from api.videos.pipeline.image_generation.schemas import ImageConfig
from api.videos.pipeline.segmentation.schemas import AnySegmentEffect
from api.videos.pipeline.tts.schemas import WordTimestamp

BUNDLED_FONT = str(
    Path(__file__).resolve().parent.parent.parent.parent / "fonts" / "Montserrat-Bold.ttf"
)


class TextStyle(BaseModel):
    """Style config for a text overlay (captions, top text)."""

    font_path: str = BUNDLED_FONT
    font_size: int = 72
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 4
    y_position: float = 0.5
    max_chars: int = 30


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
