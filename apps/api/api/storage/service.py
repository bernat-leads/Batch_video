"""Cloudflare R2 storage service (S3-compatible)."""

import io
import logging
import zipfile
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from api.core.exceptions import StorageError
from api.deps.storage import S3ClientDep
from api.settings import settings
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class StorageService:
    """S3-compatible client for Cloudflare R2."""

    def __init__(self, client: S3ClientDep) -> None:
        self._client = client
        self._bucket = settings.R2_BUCKET_NAME

    @pipeline_retry()
    def upload_file(self, key: str, data: bytes, content_type: str) -> None:
        """Upload a file to R2 storage."""
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            logger.debug("Uploaded %s (%d bytes, %s)", key, len(data), content_type)
        except Exception as e:
            raise StorageError("upload", key, cause=e) from e

    @pipeline_retry()
    def download_file(self, key: str) -> bytes:
        """Download a file from R2 storage."""
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            data = response["Body"].read()
            logger.debug("Downloaded %s (%d bytes)", key, len(data))
            return data
        except Exception as e:
            raise StorageError("download", key, cause=e) from e

    def stream_file(
        self, key: str, chunk_size: int = 1024 * 1024
    ) -> Generator[bytes, None, None]:
        """Stream a file from R2 in chunks."""
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"]
            while chunk := body.read(chunk_size):
                yield chunk
        except Exception as error:
            raise StorageError("download", key, cause=error) from error

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for a file."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_file(self, key: str) -> None:
        """Delete a file from R2 storage."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
            logger.debug("Deleted %s", key)
        except Exception as e:
            raise StorageError("delete", key, cause=e) from e

    def stream_zip(self, files: list[tuple[str, str]]) -> Generator[bytes, None, None]:
        """Build a ZIP in memory and yield it as a single chunk.

        Args:
            files: list of (r2_key, archive_filename) tuples.
        """
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for r2_key, archive_name in files:
                try:
                    data = self.download_file(r2_key)
                    zf.writestr(archive_name, data)
                except Exception as error:
                    logger.warning("ZIP: failed to download %s: %s", r2_key, error)
                    continue
        buffer.seek(0)
        yield buffer.read()

    def delete_prefix(self, prefix: str) -> int:
        """Delete all files under a prefix. Returns count of deleted objects."""
        deleted = 0
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            objects = page.get("Contents", [])
            if not objects:
                continue
            self._client.delete_objects(
                Bucket=self._bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
            )
            deleted += len(objects)
        logger.info("Deleted %d files under prefix '%s'", deleted, prefix)
        return deleted


StorageDep = Annotated[StorageService, Depends()]
