"""Event service for SSE streaming via Redis Pub/Sub."""

import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, ValidationError

from api.deps.redis import AsyncRedisDep

logger = logging.getLogger(__name__)


class EventService:
    """Subscribe to Redis Pub/Sub channels for SSE streaming."""

    def __init__(self, client: AsyncRedisDep) -> None:
        self._client = client

    async def emit(self, channel: str, event: BaseModel) -> None:
        """Publish a Pydantic event to a Redis channel."""
        await self._client.publish(channel, event.model_dump_json())

    async def subscribe(
        self,
        channel: str,
        schema: type[BaseModel],
    ) -> AsyncGenerator[BaseModel, None]:
        """Subscribe to a Redis channel and yield validated Pydantic events."""
        pubsub = self._client.pubsub()
        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    yield schema.model_validate_json(message["data"])
                except (ValidationError, ValueError):
                    logger.warning(
                        "Invalid event on channel %s: %s",
                        channel,
                        message["data"][:200],
                    )
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()


EventServiceDep = Annotated[EventService, Depends()]
