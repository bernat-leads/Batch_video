"""Abstract video editor."""

from abc import ABC, abstractmethod

from api.videos.pipeline.video_editor.schemas import AssemblyInput, EditResult


class VideoEditor(ABC):
    """Abstract video editor — subclass for different rendering backends."""

    @abstractmethod
    def assemble_video(self, assembly_input: AssemblyInput) -> EditResult:
        """Assemble final video from assembly input data."""
        ...
