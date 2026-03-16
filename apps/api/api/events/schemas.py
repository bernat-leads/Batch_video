"""Base event schemas — shared across domains."""

import enum

from pydantic import BaseModel


class EventType(str, enum.Enum):
    video_progress = "video_progress"
    batch_progress = "batch_progress"


class EventChannel(str, enum.Enum):
    video = "pipeline:video:{video_id}"
    batch = "pipeline:batch:{batch_id}"


class BaseEvent(BaseModel):
    """Base event — all events carry a type."""

    type: EventType
