"""Cloudflare R2 storage service (S3-compatible)."""

from typing import Annotated

import boto3
from fastapi import Depends

from api.settings import settings


class StorageService:
    """S3-compatible client for Cloudflare R2."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self._bucket = settings.R2_BUCKET_NAME

    def upload_file(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def download_file(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_file(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)


def get_storage() -> StorageService:
    return StorageService()


StorageDep = Annotated[StorageService, Depends(get_storage)]
