"""S3 client and file upload validation dependencies."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Annotated, Protocol, runtime_checkable

import boto3
from fastapi import Depends, HTTPException, UploadFile

from api.settings import settings


@runtime_checkable
class S3Client(Protocol):
    """Protocol for S3-compatible client methods used in this project."""

    def put_object(
        self, *, Bucket: str, Key: str, Body: bytes, ContentType: str
    ) -> dict: ...
    def get_object(self, *, Bucket: str, Key: str) -> dict: ...
    def generate_presigned_url(
        self, method: str, Params: dict, ExpiresIn: int
    ) -> str: ...
    def delete_object(self, *, Bucket: str, Key: str) -> dict: ...
    def delete_objects(self, *, Bucket: str, Delete: dict) -> dict: ...
    def get_paginator(self, operation: str) -> object: ...


s3_client: S3Client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    region_name=settings.S3_REGION,
)


def get_s3_client() -> S3Client:
    """Get the shared S3 client."""
    return s3_client


S3ClientDep = Annotated[S3Client, Depends(get_s3_client)]


# ── File upload validation ────────────────────────────────────────────


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
    """Factory that returns a file-validation dependency with custom constraints."""

    async def _validate(file: UploadFile) -> ValidatedFile:
        """Validate uploaded file extension and size."""
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
