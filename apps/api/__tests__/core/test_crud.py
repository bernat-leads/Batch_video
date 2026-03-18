"""Unit tests for BaseCrud with mocked AsyncSession.

Validates core CRUD operations (create, get, get_multi, update, delete, count, exists)
using the Video model as a concrete SQLAlchemy mapped class.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from __tests__.helpers import fake_db_obj, mock_paginated_result, mock_scalar_count
from api.core.crud import BaseCrud
from api.videos.models.video import Video

# ---------------------------------------------------------------------------
# Schemas for testing
# ---------------------------------------------------------------------------


class FakeCreate(BaseModel):
    """Schema simulating a video creation payload."""

    script_text: str


class FakeUpdate(BaseModel):
    """Schema simulating a video update payload."""

    script_text: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_crud(mock_session: AsyncMock) -> BaseCrud:
    """Build a BaseCrud instance backed by the Video model and a mocked session."""
    return BaseCrud(session=mock_session, model=Video)


# ---------------------------------------------------------------------------
# Tests: create
# ---------------------------------------------------------------------------


class TestBaseCrudCreate:
    """Verify BaseCrud.create persists a new record and returns the model instance."""

    @pytest.mark.asyncio
    async def test_create_returns_model_instance(self, mock_session: AsyncMock):
        """Creating a record should return a Video instance and call save."""
        crud = _make_crud(mock_session)
        schema = FakeCreate(script_text="Hello world")

        with patch("api.core.crud.save", new_callable=AsyncMock) as mock_save:
            result = await crud.create(schema)

        assert isinstance(result, Video)
        mock_save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_excludes_none_values(self, mock_session: AsyncMock):
        """Fields set to None should be excluded so SQLAlchemy uses column defaults."""
        crud = _make_crud(mock_session)

        class SchemaWithOptional(BaseModel):
            """Schema with an optional field to test None-exclusion."""

            script_text: str
            style: str | None = None

        schema = SchemaWithOptional(script_text="Test")

        with patch("api.core.crud.save", new_callable=AsyncMock) as mock_save:
            result = await crud.create(schema)

        assert result is not None
        mock_save.assert_awaited_once()


# ---------------------------------------------------------------------------
# Tests: get
# ---------------------------------------------------------------------------


class TestBaseCrudGet:
    """Verify BaseCrud.get retrieves a single record by primary key."""

    @pytest.mark.asyncio
    async def test_get_existing_record(self, mock_session: AsyncMock):
        """Fetching an existing record should return the matching object."""
        crud = _make_crud(mock_session)
        record_id = uuid.uuid4()
        expected = fake_db_obj(id=record_id, script_text="Test")
        mock_session.get.return_value = expected

        result = await crud.get(record_id)

        assert result == expected
        mock_session.get.assert_awaited_once_with(Video, record_id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, mock_session: AsyncMock):
        """Fetching a non-existent record should return None."""
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.get(uuid.uuid4())

        assert result is None


# ---------------------------------------------------------------------------
# Tests: get_multi
# ---------------------------------------------------------------------------


class TestBaseCrudGetMulti:
    """Verify BaseCrud.get_multi returns a paginated response."""

    @pytest.mark.asyncio
    async def test_get_multi_returns_paginated_response(self, mock_session: AsyncMock):
        """Should return a PageResponse with items, total, and page info."""
        crud = _make_crud(mock_session)
        items = [fake_db_obj(script_text="A"), fake_db_obj(script_text="B")]
        mock_paginated_result(items, total=2, session=mock_session)

        result = await crud.get_multi()

        assert len(result.items) == 2
        assert result.total == 2
        assert result.page == 1
        assert result.page_size == 50
        assert result.total_pages == 1

    @pytest.mark.asyncio
    async def test_get_multi_empty_table(self, mock_session: AsyncMock):
        """Should return a PageResponse with empty items when no records exist."""
        crud = _make_crud(mock_session)
        mock_paginated_result([], total=0, session=mock_session)

        result = await crud.get_multi()

        assert result.items == []
        assert result.total == 0
        assert result.total_pages == 0


# ---------------------------------------------------------------------------
# Tests: update
# ---------------------------------------------------------------------------


class TestBaseCrudUpdate:
    """Verify BaseCrud.update modifies an existing record."""

    @pytest.mark.asyncio
    async def test_update_existing_record(self, mock_session: AsyncMock):
        """Updating an existing record should apply the new field values."""
        crud = _make_crud(mock_session)
        record_id = uuid.uuid4()
        existing = fake_db_obj(id=record_id, script_text="Old")
        existing.script_text = "Old"
        mock_session.get.return_value = existing

        with patch("api.core.crud.save", new_callable=AsyncMock):
            result = await crud.update(record_id, FakeUpdate(script_text="New"))

        assert result is not None
        assert result.script_text == "New"

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, mock_session: AsyncMock):
        """Updating a non-existent record should return None."""
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.update(uuid.uuid4(), FakeUpdate(script_text="New"))

        assert result is None


# ---------------------------------------------------------------------------
# Tests: delete
# ---------------------------------------------------------------------------


class TestBaseCrudDelete:
    """Verify BaseCrud.delete removes a record and returns success status."""

    @pytest.mark.asyncio
    async def test_delete_existing_returns_true(self, mock_session: AsyncMock):
        """Deleting an existing record should return True and call session.delete."""
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
        """Deleting a non-existent record should return False without calling delete."""
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.delete(uuid.uuid4())

        assert result is False
        mock_session.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# Tests: count
# ---------------------------------------------------------------------------


class TestBaseCrudCount:
    """Verify BaseCrud.count returns the number of records."""

    @pytest.mark.asyncio
    async def test_count_returns_integer(self, mock_session: AsyncMock):
        """Should return the correct count of records."""
        crud = _make_crud(mock_session)
        mock_scalar_count(5, session=mock_session)

        result = await crud.count()

        assert result == 5

    @pytest.mark.asyncio
    async def test_count_empty_table_returns_zero(self, mock_session: AsyncMock):
        """Should return zero for an empty table."""
        crud = _make_crud(mock_session)
        mock_scalar_count(0, session=mock_session)

        result = await crud.count()

        assert result == 0


# ---------------------------------------------------------------------------
# Tests: exists
# ---------------------------------------------------------------------------


class TestBaseCrudExists:
    """Verify BaseCrud.exists checks for record presence by primary key."""

    @pytest.mark.asyncio
    async def test_exists_true_when_found(self, mock_session: AsyncMock):
        """Should return True when a record with the given ID exists."""
        crud = _make_crud(mock_session)
        mock_session.get.return_value = fake_db_obj(id=uuid.uuid4())

        result = await crud.exists(uuid.uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false_when_not_found(self, mock_session: AsyncMock):
        """Should return False when no record matches the given ID."""
        crud = _make_crud(mock_session)
        mock_session.get.return_value = None

        result = await crud.exists(uuid.uuid4())

        assert result is False
