"""Tests for EventService edge cases."""

from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from api.events.service import EventService


class TestEmit:
    @pytest.mark.asyncio
    async def test_emit_publishes_json_to_channel(self):
        client = AsyncMock()
        service = EventService(client)

        class FakeEvent(BaseModel):
            msg: str

        await service.emit("test-channel", FakeEvent(msg="hello"))
        client.publish.assert_called_once()
        args = client.publish.call_args
        assert args[0][0] == "test-channel"
        assert "hello" in args[0][1]

    @pytest.mark.asyncio
    async def test_emit_propagates_redis_error(self):
        client = AsyncMock()
        client.publish.side_effect = ConnectionError("Redis down")
        service = EventService(client)

        class FakeEvent(BaseModel):
            msg: str

        with pytest.raises(ConnectionError):
            await service.emit("ch", FakeEvent(msg="hi"))


class TestSubscribe:
    @pytest.mark.asyncio
    async def test_skips_invalid_json_messages(self):
        """Invalid JSON in channel should be logged and skipped, not crash."""

        async def _fake_listen():
            yield {"type": "subscribe", "data": None}
            yield {"type": "message", "data": b"not-valid-json"}
            yield {"type": "message", "data": b'{"msg": "hello"}'}

        pubsub = AsyncMock()
        pubsub.listen = _fake_listen
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.close = AsyncMock()

        client = AsyncMock()
        client.pubsub = lambda: pubsub

        class FakeEvent(BaseModel):
            msg: str

        service = EventService(client)
        events = []
        async for event in service.subscribe("ch", FakeEvent):
            events.append(event)

        assert len(events) == 1
        assert events[0].msg == "hello"

    @pytest.mark.asyncio
    async def test_skips_non_message_types(self):
        """Subscribe ack and other non-message types should be ignored."""

        async def _fake_listen():
            yield {"type": "subscribe", "data": None}
            yield {"type": "psubscribe", "data": None}

        pubsub = AsyncMock()
        pubsub.listen = _fake_listen
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.close = AsyncMock()

        client = AsyncMock()
        client.pubsub = lambda: pubsub

        class FakeEvent(BaseModel):
            msg: str

        service = EventService(client)
        events = []
        async for event in service.subscribe("ch", FakeEvent):
            events.append(event)

        assert events == []

    @pytest.mark.asyncio
    async def test_cleanup_on_explicit_close(self):
        """Pubsub should be unsubscribed and closed when generator is explicitly closed."""

        async def _fake_listen():
            yield {"type": "message", "data": b'{"msg": "hello"}'}
            yield {"type": "message", "data": b'{"msg": "world"}'}

        pubsub = AsyncMock()
        pubsub.listen = _fake_listen
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.close = AsyncMock()

        client = AsyncMock()
        client.pubsub = lambda: pubsub

        class FakeEvent(BaseModel):
            msg: str

        service = EventService(client)
        gen = service.subscribe("ch", FakeEvent)
        await gen.__anext__()  # consume first message
        await gen.aclose()  # explicitly close

        pubsub.unsubscribe.assert_called_once_with("ch")
        pubsub.close.assert_called_once()
