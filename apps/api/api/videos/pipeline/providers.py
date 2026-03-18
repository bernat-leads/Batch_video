"""Pipeline provider container — groups interchangeable service implementations."""

from pydantic import BaseModel, ConfigDict

from api.videos.pipeline.image_generation.base import ImageGenService
from api.videos.pipeline.segmentation.base import SegmentationService
from api.videos.pipeline.tts.base import TTSService
from api.videos.pipeline.video_editor.base import VideoEditor


class PipelineProviders(BaseModel):
    """Groups pipeline service implementations for injection."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    tts: TTSService
    segmentation: SegmentationService
    image_gen: ImageGenService
    editor: VideoEditor
