"""Test helpers — shared mock utilities."""

from unittest.mock import AsyncMock, MagicMock


def fake_db_obj(**kwargs):
    """Create a fake database object with the given attributes."""
    obj = MagicMock()
    for key, value in kwargs.items():
        setattr(obj, key, value)
    return obj


def mock_scalars_result(items: list, *, session: AsyncMock):
    """Mock session.execute() to return scalars().all() with the given items."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = items
    session.execute.return_value = mock_result


def mock_scalar_count(count: int, *, session: AsyncMock):
    """Mock session.execute() to return scalar_one() with a count value."""
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = count
    session.execute.return_value = mock_result


def mock_paginated_result(items: list, total: int, *, session: AsyncMock):
    """Mock session.execute() for paginated queries (count + select)."""
    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = items

    session.execute = AsyncMock(side_effect=[count_result, items_result])
