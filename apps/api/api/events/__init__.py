"""Events module — base schemas, event service, SSE routes."""

from api.events.schemas import BaseEvent, EventChannel, EventType
from api.events.service import EventService, EventServiceDep

__all__ = [
    "BaseEvent",
    "EventChannel",
    "EventService",
    "EventServiceDep",
    "EventType",
]
