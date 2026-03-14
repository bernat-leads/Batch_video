"""File upload validation dependency."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Annotated

from fastapi import Depends, HTTPException, UploadFile

from api.settings import settings


@dataclass(frozen=True, slots=True)
class ValidatedFile:
    """An uploaded file that has passed extension and size validation."""

    filename: str
    contents: bytes
    extension: str


def ValidateUpload(
    allowed_extensions: set[str] = settings.UPLOAD_ALLOWED_EXTENSIONS,
    max_size_bytes: int = settings.UPLOAD_MAX_FILE_SIZE,
):
    """Factory that returns a file-validation dependency with custom constraints.

    Usage:
        validated_file: ValidatedFileDep                                        # project defaults
        validated_file: Annotated[ValidatedFile, Depends(ValidateUpload(...))]  # custom
    """
    async def _validate(file: UploadFile) -> ValidatedFile:
        if not file.filename:
            raise HTTPException(400, "Filename is required")

        ext = PurePosixPath(file.filename).suffix.lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                400,
                f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(allowed_extensions))}",
            )

        contents = await file.read()
        if len(contents) > max_size_bytes:
            raise HTTPException(
                400,
                f"File too large. Max {max_size_bytes // 1024 // 1024}MB",
            )

        return ValidatedFile(filename=file.filename, contents=contents, extension=ext)

    return _validate


ValidatedFileDep = Annotated[ValidatedFile, Depends(ValidateUpload())]
