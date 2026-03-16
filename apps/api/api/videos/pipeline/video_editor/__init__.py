"""Stage 4: Video editing and assembly."""

from api.videos.pipeline.video_editor.base import VideoTemplate
from api.videos.pipeline.video_editor.moviepy_tiktok_ad import MoviePyTikTokAdTemplate
from api.videos.pipeline.video_editor.schemas import CaptionWord, EditResult, Segment

__all__ = [
    "CaptionWord",
    "EditResult",
    "MoviePyTikTokAdTemplate",
    "Segment",
    "VideoTemplate",
]
