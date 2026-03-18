"""Tests for batch file parsing — valid/invalid rows, column mapping, edge cases."""

import io

import pandas as pd
import pytest

from api.batches.tasks import VIDEO_FIELDS
from api.parser import PandasFileParser, ParsedRow


def _parse(
    data: bytes,
    name: str = "f.csv",
    column_mapping: dict[str, str] | None = None,
) -> list[ParsedRow]:
    return PandasFileParser(data, name, column_mapping or {}, VIDEO_FIELDS).parse()


class TestEmptyFileBatchStatus:
    """Parsing files with no data rows returns an empty list."""

    def test_empty_file_returns_no_rows(self):
        df = pd.DataFrame({"script_text": []})
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        assert _parse(buf.getvalue(), "empty.csv") == []


class TestAllRowsInvalidBatch:
    """All rows missing required fields are marked invalid."""

    def test_all_invalid_rows(self):
        csv = "script_text,voice_id\n,v1\n,v2\n,v3".encode()
        rows = _parse(csv)
        assert len(rows) == 3
        assert all(not r.is_valid for r in rows)


class TestValidRowParsing:
    """Valid CSV rows produce ParsedRow objects with correct data."""

    @pytest.mark.parametrize(
        "csv_content,expected_data",
        [
            pytest.param(
                "script_text\nHello world",
                {"script_text": "Hello world", "voice_id": "", "style": "", "top_text": ""},
                id="minimal-required-field-only",
            ),
            pytest.param(
                "script_text,voice_id,style,top_text\nTest script,voice-1,cinematic,Buy Now",
                {
                    "script_text": "Test script",
                    "voice_id": "voice-1",
                    "style": "cinematic",
                    "top_text": "Buy Now",
                },
                id="all-fields-populated",
            ),
            pytest.param(
                "script_text,voice_id\nSome text,",
                {"script_text": "Some text", "voice_id": "", "style": "", "top_text": ""},
                id="optional-fields-default-to-empty-string",
            ),
        ],
    )
    def test_valid_row_data(self, csv_content: str, expected_data: dict[str, str]):
        rows = _parse(csv_content.encode())
        assert len(rows) == 1
        assert rows[0].is_valid is True
        assert rows[0].data == expected_data
        assert rows[0].error_message is None


class TestMixedValidInvalidRows:
    """Files with both valid and invalid rows are parsed correctly."""

    def test_mixed_rows_report_correct_counts(self):
        csv = "script_text,voice_id\nHello,v1\n,v2\nWorld,v3".encode()
        rows = _parse(csv)
        valid = [r for r in rows if r.is_valid]
        invalid = [r for r in rows if not r.is_valid]
        assert len(valid) == 2
        assert len(invalid) == 1
        assert valid[0].data["script_text"] == "Hello"
        assert valid[1].data["script_text"] == "World"


class TestColumnMapping:
    """Column mapping renames source columns to expected field names."""

    @pytest.mark.parametrize(
        "source_col,mapping,expected_script",
        [
            pytest.param(
                "my_script",
                {"script_text": "my_script"},
                "Test text",
                id="single-column-remap",
            ),
            pytest.param(
                "Script Text",
                {"script_text": "Script Text"},
                "Mapped text",
                id="column-with-spaces",
            ),
        ],
    )
    def test_column_mapping_transforms_names(
        self, source_col: str, mapping: dict[str, str], expected_script: str
    ):
        csv = f"{source_col}\n{expected_script}".encode()
        rows = _parse(csv, column_mapping=mapping)
        assert len(rows) == 1
        assert rows[0].is_valid is True
        assert rows[0].data["script_text"] == expected_script

    def test_multiple_columns_remapped(self):
        csv = "my_script,my_voice\nHello,voice-1".encode()
        mapping = {"script_text": "my_script", "voice_id": "my_voice"}
        rows = _parse(csv, column_mapping=mapping)
        assert rows[0].data["script_text"] == "Hello"
        assert rows[0].data["voice_id"] == "voice-1"


class TestWhitespaceHandling:
    """Leading/trailing whitespace in cell values is stripped."""

    def test_strips_whitespace_from_values(self):
        csv = "script_text\n  Hello world  ".encode()
        rows = _parse(csv)
        assert rows[0].data["script_text"] == "Hello world"
