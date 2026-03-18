"""Tests for EventService — emit/subscribe behaviors via mocked Redis Pub/Sub."""

from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from api.events.service import EventService


class FakeEvent(BaseModel):
    """Shared test event schema."""

    msg: str


def _make_pubsub(listen_fn) -> AsyncMock:
    """Build a mock pubsub with a custom listen async generator."""
    pubsub = AsyncMock()
    pubsub.listen = listen_fn
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.close = AsyncMock()
    return pubsub


def _make_client(pubsub: AsyncMock) -> AsyncMock:
    """Build a mock Redis client that returns the given pubsub."""
    client = AsyncMock()
    client.pubsub = lambda: pubsub
    return client


class TestEmit:
    """Verify EventService.emit publishes serialized JSON to the correct channel."""

    async def test_emit_publishes_json_to_channel(self):
        client = AsyncMock()
        service = EventService(client)

        await service.emit("test-channel", FakeEvent(msg="hello"))
        client.publish.assert_called_once()
        args = client.publish.call_args
        assert args[0][0] == "test-channel"
        assert "hello" in args[0][1]

    async def test_emit_propagates_redis_error(self):
        client = AsyncMock()
        client.publish.side_effect = ConnectionError("Redis down")
        service = EventService(client)

        with pytest.raises(ConnectionError, match="Redis down"):
            await service.emit("ch", FakeEvent(msg="hi"))


class TestSubscribe:
    """Verify EventService.subscribe filters, validates, and yields events."""

    @pytest.mark.parametrize(
        "messages,expected_msgs",
        [
            pytest.param(
                [
                    {"type": "subscribe", "data": None},
                    {"type": "message", "data": b"not-valid-json"},
                    {"type": "message", "data": b'{"msg": "hello"}'},
                ],
                ["hello"],
                id="skips-invalid-json",
            ),
            pytest.param(
                [
                    {"type": "subscribe", "data": None},
                    {"type": "psubscribe", "data": None},
                ],
                [],
                id="skips-non-message-types",
            ),
            pytest.param(
                [
                    {"type": "message", "data": b'{"msg": "first"}'},
                    {"type": "message", "data": b'{"msg": "second"}'},
                ],
                ["first", "second"],
                id="yields-all-valid-messages",
            ),
        ],
    )
    async def test_subscribe_filters_messages(
        self,
        messages: list[dict[str, object]],
        expected_msgs: list[str],
    ):
        async def _fake_listen():
            for m in messages:
                yield m

        pubsub = _make_pubsub(_fake_listen)
        client = _make_client(pubsub)
        service = EventService(client)

        events: list[FakeEvent] = []
        async for event in service.subscribe("ch", FakeEvent):
            events.append(event)

        assert [e.msg for e in events] == expected_msgs

    async def test_cleanup_on_explicit_close(self):
        """Pubsub should be unsubscribed and closed when generator is explicitly closed."""

        async def _fake_listen():
            yield {"type": "message", "data": b'{"msg": "hello"}'}
            yield {"type": "message", "data": b'{"msg": "world"}'}

        pubsub = _make_pubsub(_fake_listen)
        client = _make_client(pubsub)
        service = EventService(client)

        gen = service.subscribe("ch", FakeEvent)
        event = await gen.__anext__()
        assert event.msg == "hello"
        await gen.aclose()

        pubsub.unsubscribe.assert_called_once_with("ch")
        pubsub.close.assert_called_once()
