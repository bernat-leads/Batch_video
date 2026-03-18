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
        """Initialize with raw file bytes, filename, column mapping, and field definitions."""
        self._file_bytes = file_bytes
        self._file_name = file_name
        self._column_mapping = column_mapping
        self._fields = fields

    def parse(self) -> list[ParsedRow]:
        """Read file, apply mapping, validate, and return parsed rows."""
        logger.info(
            "Parsing file '%s' (%d bytes)", self._file_name, len(self._file_bytes)
        )

        dataframe = self._read_dataframe()
        dataframe = self._apply_column_mapping(dataframe)
        self._validate_required_columns(dataframe)
        rows = self._build_rows(dataframe)

        valid_count = sum(1 for row in rows if row.is_valid)
        logger.info(
            "Parsed %d rows from '%s' (%d valid, %d invalid)",
            len(rows),
            self._file_name,
            valid_count,
            len(rows) - valid_count,
        )
        return rows

    def _read_dataframe(self) -> pd.DataFrame:
        """Read raw bytes into a pandas DataFrame."""
        buffer = io.BytesIO(self._file_bytes)
        extension = PurePosixPath(self._file_name).suffix.lower()

        try:
            match extension:
                case ".csv":
                    return pd.read_csv(buffer)
                case ".xlsx" | ".xls":
                    return pd.read_excel(buffer, engine="openpyxl")
                case _:
                    raise BatchParseError(f"Unsupported file format: {extension}")
        except BatchParseError:
            raise
        except Exception as error:
            raise BatchParseError(
                f"Failed to read '{self._file_name}': {error}"
            ) from error

    def _apply_column_mapping(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Rename columns according to the user-provided mapping."""
        reverse = {value: key for key, value in self._column_mapping.items() if value}
        if reverse:
            logger.debug("Applying column mapping: %s", reverse)
        return dataframe.rename(columns=reverse)

    def _validate_required_columns(self, dataframe: pd.DataFrame) -> None:
        """Raise if any required columns are missing after mapping."""
        required = {field.name for field in self._fields if field.required}
        missing = required - set(dataframe.columns)
        if missing:
            raise BatchParseError(
                f"Required column(s) {sorted(missing)} not found after mapping. "
                f"Available: {sorted(dataframe.columns)}"
            )

    def _build_rows(self, dataframe: pd.DataFrame) -> list[ParsedRow]:
        """Validate and convert DataFrame rows into ParsedRow objects (vectorized)."""
        if dataframe.empty:
            return []

        field_names = [field.name for field in self._fields]
        required_names = [field.name for field in self._fields if field.required]

        # Ensure all fields exist, fill missing with defaults, clean strings
        for field in self._fields:
            if field.name not in dataframe.columns:
                dataframe[field.name] = field.default
            else:
                dataframe[field.name] = (
                    dataframe[field.name].fillna(field.default).astype(str).str.strip()
                )

        # Vectorized validity check: all required fields must be non-empty
        is_valid = pd.Series(True, index=dataframe.index)
        for name in required_names:
            is_valid &= dataframe[name] != ""

        # Build error messages: collect names of empty required fields per row
        if required_names:
            empty_flags = pd.DataFrame(
                {
                    name: dataframe[name].eq("").map({True: name, False: ""})
                    for name in required_names
                }
            )
            error_messages = empty_flags.apply(
                lambda row: ", ".join(value for value in row if value),
                axis=1,
            )
        else:
            error_messages = pd.Series("", index=dataframe.index)

        # Fill placeholder text for invalid required fields
        for name in required_names:
            empty_mask = dataframe[name] == ""
            dataframe.loc[empty_mask, name] = "Row " + (
                dataframe.index[empty_mask] + 2
            ).astype(str)

        # Slice only needed columns and convert to list of ParsedRow
        data_df = dataframe[field_names]
        records = data_df.to_dict(orient="records")
        valid_list = is_valid.tolist()
        error_list = error_messages.tolist()

        return [
            ParsedRow(
                data=record,
                is_valid=valid,
                error_message=f"Empty required field(s): {error}"
                if not valid
                else None,
            )
            for record, valid, error in zip(records, valid_list, error_list)
        ]
