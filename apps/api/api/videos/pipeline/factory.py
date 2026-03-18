"""Factory for creating pipeline providers from settings."""

from api.videos.pipeline.image_generation.gemini import GeminiImageGenService
from api.videos.pipeline.providers import PipelineProviders
from api.videos.pipeline.segmentation.claude import ClaudeSegmentationService
from api.videos.pipeline.tts.elevenlabs import ElevenLabsTTSService
from api.videos.pipeline.video_editor.effects import NumpyEffectService
from api.videos.pipeline.video_editor.moviepy_editor import MoviePyVideoEditor


def create_pipeline_providers() -> PipelineProviders:
    """Create pipeline providers. Centralized — swap implementations here."""
    return PipelineProviders(
        tts=ElevenLabsTTSService(),
        segmentation=ClaudeSegmentationService(),
        image_gen=GeminiImageGenService(),
        editor=MoviePyVideoEditor(NumpyEffectService()),
    )
