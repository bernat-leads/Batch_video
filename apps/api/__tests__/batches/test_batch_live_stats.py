"""Tests for batch live stats — column_property subqueries on Batch model."""

import pytest

from api.batches.enums import BatchStatus
from api.batches.models.batch import Batch
from api.batches.schemas import BatchRead


class TestBatchModelHasComputedProperties:
    """Batch model should expose computed stats as column_property."""

    @pytest.mark.parametrize(
        "attr",
        [
            "total_videos",
            "completed_count",
            "failed_count",
            "pending_count",
            "duration_ms",
            "total_cost_usd",
            "status",
        ],
    )
    def test_batch_has_computed_attribute(self, attr):
        """Batch model should have the computed column_property."""
        assert hasattr(Batch, attr)

    def test_batch_has_no_cached_columns(self):
        """Batch model should NOT have these as mapped_column (they're column_property)."""
        mapped_columns = {
            col.key for col in Batch.__table__.columns
        }
        # These should NOT be in the actual table columns
        assert "total_videos" not in mapped_columns
        assert "completed_count" not in mapped_columns
        assert "failed_count" not in mapped_columns
        assert "pending_count" not in mapped_columns
        assert "duration_ms" not in mapped_columns
        assert "total_cost_usd" not in mapped_columns
        assert "status" not in mapped_columns

    def test_batch_table_has_core_columns(self):
        """Batch table should have the non-computed columns."""
        mapped_columns = {
            col.key for col in Batch.__table__.columns
        }
        assert "id" in mapped_columns
        assert "name" in mapped_columns
        assert "column_mapping" in mapped_columns
        assert "file_name" in mapped_columns
        assert "file_key" in mapped_columns
        assert "error_message" in mapped_columns


class TestBatchReadSchema:
    """BatchRead schema should accept computed stats fields."""

    def test_batch_read_accepts_all_stat_fields(self):
        import uuid
        from datetime import datetime

        batch = BatchRead(
            id=uuid.uuid4(),
            name="test",
            status=BatchStatus.completed,
            total_videos=5,
            completed_count=3,
            failed_count=2,
            pending_count=0,
            duration_ms=10000,
            total_cost_usd=0.05,
            created_at=datetime.now(),
        )
        assert batch.total_videos == 5
        assert batch.completed_count == 3
        assert batch.total_cost_usd == 0.05

    def test_batch_read_no_model_costs(self):
        """BatchRead should not have model_costs field (removed)."""
        assert "model_costs" not in BatchRead.model_fields


class TestDeriveStatusLogic:
    """Test the SQL case expression logic (mirrored in Python)."""

    @pytest.mark.parametrize(
        "total, pending, failed, expected",
        [
            pytest.param(0, 0, 0, BatchStatus.failed, id="zero-total"),
            pytest.param(5, 5, 0, BatchStatus.processing, id="all-processing"),
            pytest.param(5, 1, 0, BatchStatus.processing, id="one-pending"),
            pytest.param(5, 0, 0, BatchStatus.completed, id="all-finished"),
            pytest.param(5, 0, 2, BatchStatus.completed, id="mixed"),
            pytest.param(5, 0, 5, BatchStatus.failed, id="all-failed"),
            pytest.param(1, 0, 1, BatchStatus.failed, id="single-failed"),
        ],
    )
    def test_status_derivation(self, total, pending, failed, expected):
        """Python mirror of the SQL case expression in Batch.status."""
        if total == 0:
            status = BatchStatus.failed
        elif pending > 0:
            status = BatchStatus.processing
        elif failed == total:
            status = BatchStatus.failed
        else:
            status = BatchStatus.completed
        assert status == expected
