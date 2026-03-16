"""Custom exception hierarchy for the video pipeline."""


class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""


class PipelineStageError(PipelineError):
    """A pipeline stage (TTS, segmentation, image gen, assembly) failed."""

    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        super().__init__(f"{stage}: {message}")


class StorageError(PipelineError):
    """R2/S3 storage operation failed (upload, download, delete)."""

    def __init__(
        self, operation: str, key: str, cause: Exception | None = None
    ) -> None:
        self.operation = operation
        self.key = key
        self.cause = cause
        super().__init__(f"Storage {operation} failed for '{key}'")


class BatchParseError(PipelineError):
    """Batch file parsing failed."""


class SegmentationEmptyError(PipelineStageError):
    """Segmentation returned zero segments."""

    def __init__(self) -> None:
        super().__init__("segmentation", "returned no segments for the given script")
