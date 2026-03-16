"""Pandas-based file parser for Excel/CSV files."""

import io
import logging
from pathlib import PurePosixPath

import pandas as pd

from api.core.exceptions import BatchParseError
from api.parser.base import FieldDef, FileParser, ParsedRow

logger = logging.getLogger(__name__)


class PandasFileParser(FileParser):
    """Parses Excel/CSV files into rows using pandas."""

    def __init__(
        self,
        file_bytes: bytes,
        file_name: str,
        column_mapping: dict[str, str],
        fields: tuple[FieldDef, ...],
    ) -> None:
        self._file_bytes = file_bytes
        self._file_name = file_name
        self._column_mapping = column_mapping
        self._fields = fields

    def parse(self) -> list[ParsedRow]:
        logger.info(
            "Parsing file '%s' (%d bytes)", self._file_name, len(self._file_bytes)
        )
        df = self._read_dataframe()
        df = self._apply_column_mapping(df)
        self._validate_required_columns(df)
        rows = self._build_rows(df)
        valid = sum(1 for r in rows if r.is_valid)
        logger.info(
            "Parsed %d rows from '%s' (%d valid, %d invalid)",
            len(rows),
            self._file_name,
            valid,
            len(rows) - valid,
        )
        return rows

    def _read_dataframe(self) -> pd.DataFrame:
        buf = io.BytesIO(self._file_bytes)
        ext = PurePosixPath(self._file_name).suffix.lower()

        try:
            match ext:
                case ".csv":
                    return pd.read_csv(buf)
                case ".xlsx" | ".xls":
                    return pd.read_excel(buf, engine="openpyxl")
                case _:
                    raise BatchParseError(f"Unsupported file format: {ext}")
        except BatchParseError:
            raise
        except Exception as e:
            raise BatchParseError(f"Failed to read '{self._file_name}': {e}") from e

    def _apply_column_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        reverse = {v: k for k, v in self._column_mapping.items() if v}
        if reverse:
            logger.debug("Applying column mapping: %s", reverse)
        return df.rename(columns=reverse)

    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        required = {f.name for f in self._fields if f.required}
        missing = required - set(df.columns)
        if missing:
            raise BatchParseError(
                f"Required column(s) {sorted(missing)} not found after mapping. "
                f"Available: {sorted(df.columns)}"
            )

    def _build_rows(self, df: pd.DataFrame) -> list[ParsedRow]:
        for f in self._fields:
            if f.name not in df.columns:
                df[f.name] = f.default
            else:
                df[f.name] = df[f.name].fillna(f.default).astype(str).str.strip()

        field_names = [f.name for f in self._fields]
        required_names = [f.name for f in self._fields if f.required]

        rows: list[ParsedRow] = []
        for idx, raw in df.iterrows():
            data = {name: raw[name] for name in field_names}

            missing = [name for name in required_names if not data[name]]
            if missing:
                for name in missing:
                    data[name] = f"Row {idx + 2}"
                rows.append(
                    ParsedRow(
                        data=data,
                        is_valid=False,
                        error_message=f"Empty required field(s): {', '.join(missing)}",
                    )
                )
            else:
                rows.append(ParsedRow(data=data, is_valid=True, error_message=None))

        return rows
