"""Enums for batch status fields."""

import enum


class BatchStatus(str, enum.Enum):
    """Status of a batch in the pipeline."""

    processing = "processing"
    completed = "completed"
    failed = "failed"
