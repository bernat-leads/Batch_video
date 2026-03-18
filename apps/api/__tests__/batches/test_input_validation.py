"""Tests for batch input validation rules.

Verifies that schema-level and route-level constraints reject invalid data
and accept valid data for batch-related endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from api.batches.schemas import BatchCreate, BatchUpdate


# ---------------------------------------------------------------------------
# BatchCreate validation
# ---------------------------------------------------------------------------


class TestBatchCreateValidation:
    """Business rules for creating a batch."""

    def test_empty_name_is_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            BatchCreate(
                name="",
                column_mapping={"script": "script_text"},
                file_name="test.xlsx",
            )

    def test_name_over_255_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            BatchCreate(
                name="x" * 256,
                column_mapping={"script": "script_text"},
                file_name="test.xlsx",
            )

    def test_name_at_255_chars_is_accepted(self):
        batch = BatchCreate(
            name="x" * 255,
            column_mapping={"script": "script_text"},
            file_name="test.xlsx",
        )
        assert len(batch.name) == 255

    def test_empty_file_name_is_rejected(self):
        with pytest.raises(ValidationError, match="file_name"):
            BatchCreate(
                name="My Batch",
                column_mapping={"script": "script_text"},
                file_name="",
            )

    def test_file_name_over_255_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="file_name"):
            BatchCreate(
                name="My Batch",
                column_mapping={"script": "script_text"},
                file_name="x" * 256,
            )

    def test_valid_batch_create_is_accepted(self):
        batch = BatchCreate(
            name="Campaign Q1",
            column_mapping={"script": "script_text"},
            file_name="scripts.xlsx",
        )
        assert batch.name == "Campaign Q1"
        assert batch.file_name == "scripts.xlsx"


# ---------------------------------------------------------------------------
# BatchUpdate validation
# ---------------------------------------------------------------------------


class TestBatchUpdateValidation:
    """Business rules for updating a batch."""

    def test_empty_name_update_is_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            BatchUpdate(name="")

    def test_name_over_255_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="name"):
            BatchUpdate(name="x" * 256)

    def test_none_name_is_accepted(self):
        """None means 'do not update this field'."""
        update = BatchUpdate(name=None)
        assert update.name is None

    def test_valid_name_update_is_accepted(self):
        update = BatchUpdate(name="Renamed Batch")
        assert update.name == "Renamed Batch"


# ---------------------------------------------------------------------------
# Route-level pagination validation (via test client)
# ---------------------------------------------------------------------------


class TestBatchPaginationValidation:
    """Pagination query parameters enforce bounds at the route level."""

    @pytest.fixture(scope="class")
    def authed_client(self):
        from api.app import create_application
        from api.deps.auth import get_current_session
        from fastapi.testclient import TestClient

        app = create_application()
        app.dependency_overrides[get_current_session] = lambda: {"authenticated": True}
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_page_zero_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/batches/?page=0")
        assert resp.status_code == 422

    def test_page_negative_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/batches/?page=-1")
        assert resp.status_code == 422

    def test_page_size_zero_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/batches/?page_size=0")
        assert resp.status_code == 422

    def test_page_size_over_100_returns_422(self, authed_client):
        resp = authed_client.get("/api/v1/batches/?page_size=101")
        assert resp.status_code == 422

    def test_page_size_at_100_is_accepted(self, authed_client):
        with patch(
            "api.batches.crud.BatchCrud.get_multi",
            new_callable=AsyncMock,
        ) as mock_get:
            from api.core.schemas import PageResponse

            mock_get.return_value = PageResponse.create(
                items=[], total=0, page=1, page_size=100
            )
            resp = authed_client.get("/api/v1/batches/?page_size=100")
        assert resp.status_code == 200
