"""Enums for video pipeline status fields."""

import enum


class VideoStatus(str, enum.Enum):
    """Status of a video in the pipeline."""

    processing = "processing"
    finished = "finished"
    failed = "failed"


class VideoStage(str, enum.Enum):
    """Current pipeline stage for a video."""

    queued = "queued"
    tts = "tts"
    segmentation = "segmentation"
    image_generation = "image_generation"
    assembly = "assembly"
    upload = "upload"
    done = "done"
