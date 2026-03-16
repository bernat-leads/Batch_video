"""Tests for file parser edge cases."""

import io

import pandas as pd
import pytest

from api.batches.tasks import VIDEO_FIELDS
from api.core.exceptions import BatchParseError
from api.parser import FieldDef, PandasFileParser


def _csv_bytes(content: str) -> bytes:
    return content.encode("utf-8")


def _xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _parse(data: bytes, name: str = "f.csv", mapping: dict | None = None):
    return PandasFileParser(data, name, mapping or {}, VIDEO_FIELDS).parse()


class TestUnsupportedFormat:
    def test_raises_on_txt_file(self):
        with pytest.raises(BatchParseError, match="Unsupported file format"):
            _parse(b"hello", "file.txt")

    def test_raises_on_no_extension(self):
        with pytest.raises(BatchParseError, match="Unsupported file format"):
            _parse(b"hello", "file")


class TestMissingRequiredColumns:
    def test_raises_when_script_text_missing(self):
        with pytest.raises(BatchParseError, match="script_text"):
            _parse(_csv_bytes("voice_id,style\nfoo,bar"))

    def test_column_mapping_resolves_script_text(self):
        rows = _parse(
            _csv_bytes("my_script,voice_id\nhello,v1"),
            mapping={"script_text": "my_script"},
        )
        assert rows[0].data["script_text"] == "hello"
        assert rows[0].is_valid is True

    def test_wrong_mapping_still_raises(self):
        with pytest.raises(BatchParseError, match="script_text"):
            _parse(
                _csv_bytes("col_a,col_b\nhello,v1"),
                mapping={"script_text": "nonexistent"},
            )


class TestEmptyScriptRows:
    def test_empty_script_marked_invalid(self):
        rows = _parse(_csv_bytes("script_text,voice_id\n,v1"))
        assert len(rows) == 1
        assert rows[0].is_valid is False
        assert "script_text" in rows[0].error_message

    def test_whitespace_only_script_marked_invalid(self):
        rows = _parse(_csv_bytes("script_text,voice_id\n   ,v1"))
        assert rows[0].is_valid is False

    def test_mix_valid_and_invalid(self):
        df = pd.DataFrame({"script_text": ["hello", "", "world"]})
        rows = _parse(_xlsx_bytes(df), "f.xlsx")
        assert len([r for r in rows if r.is_valid]) == 2
        assert len([r for r in rows if not r.is_valid]) == 1


class TestMissingOptionalColumns:
    def test_missing_voice_id_defaults_to_empty(self):
        rows = _parse(_csv_bytes("script_text\nhello"))
        assert rows[0].data["voice_id"] == ""

    def test_missing_top_text_defaults_to_empty(self):
        rows = _parse(_csv_bytes("script_text\nhello"))
        assert rows[0].data["top_text"] == ""


class TestXlsxParsing:
    def test_parses_xlsx(self):
        df = pd.DataFrame({"script_text": ["hello"], "voice_id": ["v1"]})
        rows = _parse(_xlsx_bytes(df), "f.xlsx")
        assert len(rows) == 1
        assert rows[0].data["script_text"] == "hello"

    def test_empty_xlsx_returns_empty_list(self):
        df = pd.DataFrame({"script_text": []})
        assert _parse(_xlsx_bytes(df), "f.xlsx") == []


class TestCorruptFile:
    def test_corrupt_xlsx_raises(self):
        with pytest.raises(Exception):
            _parse(b"\x00\x01\x02", "f.xlsx")


class TestCustomFields:
    def test_custom_fields(self):
        fields = (FieldDef(name="title", required=True), FieldDef(name="body"))
        rows = PandasFileParser(
            _csv_bytes("title,body\nHi,World"), "f.csv", {}, fields
        ).parse()
        assert rows[0].data == {"title": "Hi", "body": "World"}
