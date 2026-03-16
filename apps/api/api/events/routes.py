"""SSE endpoints for real-time pipeline progress."""

import logging
import uuid
from collections.abc import AsyncIterable

from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent

from api.deps.auth import AuthDep
from api.events.schemas import BaseEvent, EventChannel
from api.events.service import EventServiceDep
from api.videos.schemas import VideoProgressEvent

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.get("/videos/{video_id}", response_class=EventSourceResponse)
async def stream_video(
    video_id: uuid.UUID,
    _auth: AuthDep,
    service: EventServiceDep,
) -> AsyncIterable[ServerSentEvent]:
    """Stream pipeline progress for a single video."""
    logger.debug("SSE connected: video %s", video_id)
    channel = EventChannel.video.format(video_id=str(video_id))
    async for event in service.subscribe(channel, VideoProgressEvent):
        yield ServerSentEvent(data=event, event="video_progress")


@events_router.get("/batches/{batch_id}", response_class=EventSourceResponse)
async def stream_batch(
    batch_id: uuid.UUID,
    _auth: AuthDep,
    service: EventServiceDep,
) -> AsyncIterable[ServerSentEvent]:
    """Stream progress for a batch (video + batch events)."""
    logger.debug("SSE connected: batch %s", batch_id)
    channel = EventChannel.batch.format(batch_id=str(batch_id))
    async for event in service.subscribe(channel, BaseEvent):
        yield ServerSentEvent(data=event, event=event.type.value)
