"""Tests for batch input validation rules."""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from api.batches.schemas import BatchCreate, BatchUpdate

VALID_BATCH = dict(name="Campaign Q1", column_mapping={"script": "script_text"}, file_name="scripts.xlsx")


@pytest.mark.parametrize(
    "kwargs, match",
    [
        pytest.param({**VALID_BATCH, "name": ""}, "name", id="empty-name"),
        pytest.param({**VALID_BATCH, "name": "x" * 256}, "name", id="name-too-long"),
        pytest.param({**VALID_BATCH, "file_name": ""}, "file_name", id="empty-file-name"),
        pytest.param({**VALID_BATCH, "file_name": "x" * 256}, "file_name", id="file-name-too-long"),
    ],
)
def test_batch_create_rejects_invalid(kwargs, match):
    with pytest.raises(ValidationError, match=match):
        BatchCreate(**kwargs)


@pytest.mark.parametrize(
    "kwargs, assertions",
    [
        pytest.param(VALID_BATCH, {"name": "Campaign Q1", "file_name": "scripts.xlsx"}, id="valid"),
        pytest.param({**VALID_BATCH, "name": "x" * 255}, {"name": "x" * 255}, id="name-at-limit"),
    ],
)
def test_batch_create_accepts_valid(kwargs, assertions):
    batch = BatchCreate(**kwargs)
    for field, expected in assertions.items():
        assert getattr(batch, field) == expected


@pytest.mark.parametrize(
    "kwargs, match",
    [
        pytest.param(dict(name=""), "name", id="empty-name"),
        pytest.param(dict(name="x" * 256), "name", id="name-too-long"),
    ],
)
def test_batch_update_rejects_invalid(kwargs, match):
    with pytest.raises(ValidationError, match=match):
        BatchUpdate(**kwargs)


@pytest.mark.parametrize(
    "kwargs, assertions",
    [
        pytest.param(dict(name=None), {"name": None}, id="none-is-accepted"),
        pytest.param(dict(name="Renamed"), {"name": "Renamed"}, id="valid-name"),
    ],
)
def test_batch_update_accepts_valid(kwargs, assertions):
    update = BatchUpdate(**kwargs)
    for field, expected in assertions.items():
        assert getattr(update, field) == expected


class TestBatchPaginationValidation:
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

    @pytest.mark.parametrize(
        "params",
        [
            pytest.param("page=0", id="page-zero"),
            pytest.param("page=-1", id="page-negative"),
            pytest.param("page_size=0", id="page-size-zero"),
            pytest.param("page_size=101", id="page-size-over-100"),
        ],
    )
    def test_invalid_pagination_returns_422(self, authed_client, params):
        assert authed_client.get(f"/api/v1/batches/?{params}").status_code == 422

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
