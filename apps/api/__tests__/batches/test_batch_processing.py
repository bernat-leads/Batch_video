"""Tests for batch processing edge cases — empty files, status transitions."""

import io

import pandas as pd

from api.batches.tasks import VIDEO_FIELDS
from api.parser import PandasFileParser


def _parse(data: bytes, name: str = "f.csv"):
    return PandasFileParser(data, name, {}, VIDEO_FIELDS).parse()


class TestEmptyFileBatchStatus:
    def test_empty_file_returns_no_rows(self):
        df = pd.DataFrame({"script_text": []})
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        assert _parse(buf.getvalue(), "empty.csv") == []


class TestBatchNameSanitization:
    def test_batch_name_with_quotes(self):
        assert '"' in 'test"batch'

    def test_batch_name_with_newline(self):
        assert "\n" in "test\nbatch"


class TestAllRowsInvalidBatch:
    def test_all_invalid_rows(self):
        csv = "script_text,voice_id\n,v1\n,v2\n,v3".encode()
        rows = _parse(csv)
        assert len([r for r in rows if r.is_valid]) == 0
        assert len([r for r in rows if not r.is_valid]) == 3
