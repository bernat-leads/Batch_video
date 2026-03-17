"""Stage 4: Video editing and assembly."""

from api.videos.pipeline.video_editor.base import VideoEditor
from api.videos.pipeline.video_editor.moviepy_editor import MoviePyVideoEditor
from api.videos.pipeline.video_editor.schemas import (
    AssemblyInput,
    EditResult,
    Segment,
    VideoTemplate,
)

__all__ = [
    "AssemblyInput",
    "EditResult",
    "MoviePyVideoEditor",
    "Segment",
    "VideoEditor",
    "VideoTemplate",
]
