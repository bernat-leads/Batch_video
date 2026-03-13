"""Unit tests for BaseCrud with mocked AsyncSession."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from __tests__.helpers import fake_db_obj, mock_scalar_count, mock_scalars_result
from api.core.crud import BaseCrud
from api.items.models.item import Item


# ---------------------------------------------------------------------------
# Schemas for testing
# ---------------------------------------------------------------------------


class FakeCreate(BaseModel):
    title: str


class FakeUpdate(BaseModel):
    title: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_crud(mock_session: AsyncMock) -> BaseCrud:
    """Use a real mapped model (Item) so SQLAlchemy accepts it."""
    return BaseCrud(session=mock_session, model=Item)


# ---------------------------------------------------------------------------
# Tests: create
# ---------------------------------------------------------------------------


class TestBaseCrudCreate:
    @pytest.mark.asyncio
    async def test_create_returns_model_instance(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        schema = FakeCreate(title="Test Item")

        with patch("api.core.crud.save", new_callable=AsyncMock) as mock_save:
            result = await crud.create(schema)

        assert isinstance(result, Item)
        mock_save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_excludes_none_values(self, mock_session: AsyncMock):
        """Fields set to None should be excluded so SQLAlchemy uses column defaults."""
        crud = _make_crud(mock_session)

        class SchemaWithOptional(BaseModel):
            title: str
            content: str | None = None

        schema = SchemaWithOptional(title="Test")

        with patch("api.core.crud.save", new_callable=AsyncMock) as mock_save:
            result = await crud.create(schema)

        assert result is not None
        mock_save.assert_awaited_once()


# ---------------------------------------------------------------------------
# Tests: get
# ---------------------------------------------------------------------------


class TestBaseCrudGet:
    @pytest.mark.asyncio
    async def test_get_existing_record(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        record_id = uuid.uuid4()
        expected = fake_db_obj(id=record_id, title="Test")
        mock_session.get.return_value = expected

        result = await crud.get(record_id)

        assert result == expected
        mock_session.get.assert_awaited_once_with(Item, record_id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.get(uuid.uuid4())

        assert result is None


# ---------------------------------------------------------------------------
# Tests: get_multi
# ---------------------------------------------------------------------------


class TestBaseCrudGetMulti:
    @pytest.mark.asyncio
    async def test_get_multi_returns_list(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        items = [fake_db_obj(title="A"), fake_db_obj(title="B")]
        mock_scalars_result(items, session=mock_session)

        result = await crud.get_multi()

        assert len(result) == 2
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_multi_empty_table(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_scalars_result([], session=mock_session)

        result = await crud.get_multi()

        assert result == []


# ---------------------------------------------------------------------------
# Tests: update
# ---------------------------------------------------------------------------


class TestBaseCrudUpdate:
    @pytest.mark.asyncio
    async def test_update_existing_record(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        record_id = uuid.uuid4()
        existing = fake_db_obj(id=record_id, title="Old")
        existing.title = "Old"
        mock_session.get.return_value = existing

        with patch("api.core.crud.save", new_callable=AsyncMock):
            result = await crud.update(record_id, FakeUpdate(title="New"))

        assert result is not None
        assert result.title == "New"

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.update(uuid.uuid4(), FakeUpdate(title="New"))

        assert result is None


# ---------------------------------------------------------------------------
# Tests: delete
# ---------------------------------------------------------------------------


class TestBaseCrudDelete:
    @pytest.mark.asyncio
    async def test_delete_existing_returns_true(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        record_id = uuid.uuid4()
        existing = fake_db_obj(id=record_id)
        mock_session.get.return_value = existing

        result = await crud.delete(record_id)

        assert result is True
        mock_session.delete.assert_awaited_once_with(existing)
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.delete(uuid.uuid4())

        assert result is False
        mock_session.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# Tests: count
# ---------------------------------------------------------------------------


class TestBaseCrudCount:
    @pytest.mark.asyncio
    async def test_count_returns_integer(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_scalar_count(5, session=mock_session)

        result = await crud.count()

        assert result == 5

    @pytest.mark.asyncio
    async def test_count_empty_table_returns_zero(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_scalar_count(0, session=mock_session)

        result = await crud.count()

        assert result == 0


# ---------------------------------------------------------------------------
# Tests: exists
# ---------------------------------------------------------------------------


class TestBaseCrudExists:
    @pytest.mark.asyncio
    async def test_exists_true_when_found(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_session.get.return_value = fake_db_obj(id=uuid.uuid4())

        result = await crud.exists(uuid.uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false_when_not_found(self, mock_session: AsyncMock):
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.exists(uuid.uuid4())

        assert result is False
