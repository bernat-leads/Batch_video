"""Abstract file parser and shared types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FieldDef:
    """Definition of a parseable column."""

    name: str
    required: bool = False
    default: str = ""


@dataclass(frozen=True, slots=True)
class ParsedRow:
    """A single parsed row from a file."""

    data: dict[str, str]
    is_valid: bool
    error_message: str | None


class FileParser(ABC):
    """Abstract file parser — subclass for different backends (pandas, polars, etc.)."""

    @abstractmethod
    def parse(self) -> list[ParsedRow]:
        """Read, validate, and return parsed rows."""
        ...
