"""Excel/CSV file parser for batch processing.

Handles reading spreadsheet files, applying column mappings,
validating rows, and producing typed video row data.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import PurePosixPath

import pandas as pd

REQUIRED_COLUMNS = frozenset({"script_text"})


@dataclass(frozen=True, slots=True)
class VideoRowData:
    """A single parsed row from the spreadsheet, ready for persistence.

    `is_valid` is False when the row failed validation (e.g. empty script).
    The CRUD layer uses this flag to set the appropriate video status.
    """

    script_text: str
    voice_id: str
    style: str
    top_text: str | None
    prompt: str
    is_valid: bool
    error_message: str | None


class BatchFileParser:
    """Parses an uploaded file into a list of ``VideoRowData``."""

    def __init__(
        self,
        file_bytes: bytes,
        file_name: str,
        column_mapping: dict[str, str],
    ) -> None:
        self._file_bytes = file_bytes
        self._file_name = file_name
        self._column_mapping = column_mapping

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> list[VideoRowData]:
        """Read, validate, and return typed video rows.

        Raises:
            ValueError: If the file format is unsupported or the required
                column ``script_text`` is missing after mapping.
        """
        df = self._read_dataframe()
        df = self._apply_column_mapping(df)
        self._validate_required_columns(df)
        return self._build_rows(df)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_dataframe(self) -> pd.DataFrame:
        """Read the raw bytes into a pandas DataFrame."""
        buf = io.BytesIO(self._file_bytes)
        ext = PurePosixPath(self._file_name).suffix.lower()

        match ext:
            case ".csv":
                return pd.read_csv(buf)
            case ".xlsx" | ".xls":
                return pd.read_excel(buf, engine="openpyxl")
            case _:
                raise ValueError(f"Unsupported file format: {ext}")

    def _apply_column_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename spreadsheet columns according to the user-provided mapping."""
        reverse = {v: k for k, v in self._column_mapping.items() if v}
        return df.rename(columns=reverse)

    @staticmethod
    def _validate_required_columns(df: pd.DataFrame) -> None:
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            msg = (
                f"Required column(s) {sorted(missing)} not found after mapping. "
                f"Available: {sorted(df.columns)}"
            )
            raise ValueError(msg)

    @staticmethod
    def _build_rows(df: pd.DataFrame) -> list[VideoRowData]:
        """Validate and transform rows into typed ``VideoRowData`` using vectorized ops."""

        # TODO: Clean up this logic and consider using a more robust validation library if it grows. Must validate columns instead of rows.

        _COLUMNS = ("script_text", "voice_id", "style", "top_text", "prompt")
        for col in _COLUMNS:
            if col not in df.columns:
                df[col] = ""
            else:
                df[col] = df[col].fillna("").astype(str).str.strip()

        is_valid = df["script_text"] != ""
        df.loc[~is_valid, "script_text"] = "Row " + (df.index[~is_valid] + 2).astype(str)

        # Vectorize nullable fields using Python lists for clean None handling.
        top_texts = [v or None for v in df["top_text"]]
        error_messages = [None if v else "Empty script text" for v in is_valid]

        return list(map(
            VideoRowData,
            df["script_text"],
            df["voice_id"],
            df["style"],
            top_texts,
            df["prompt"],
            is_valid,
            error_messages,
        ))
