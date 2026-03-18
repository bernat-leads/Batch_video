"""Tests for StorageService — upload, download, presigned URLs, delete, ZIP response."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.responses import StreamingResponse

from api.core.exceptions import StorageError
from api.storage.service import StorageService


@pytest.fixture
def mock_s3() -> MagicMock:
    """Provide a mock S3 client with standard methods stubbed."""
    client = MagicMock()
    return client


@pytest.fixture
def storage(mock_s3: MagicMock) -> StorageService:
    """Build a StorageService backed by the mock S3 client."""
    with patch("api.storage.service.settings") as mock_settings:
        mock_settings.S3_BUCKET_NAME = "test-bucket"
        svc = StorageService(mock_s3)
    return svc


class TestUploadFile:
    """Verify upload_file delegates to S3 put_object and wraps errors."""

    def test_upload_success(self, storage: StorageService, mock_s3: MagicMock):
        storage.upload_file("videos/test.mp4", b"data", "video/mp4")

        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="videos/test.mp4",
            Body=b"data",
            ContentType="video/mp4",
        )

    def test_upload_wraps_s3_error_in_storage_error(
        self, storage: StorageService, mock_s3: MagicMock
    ):
        mock_s3.put_object.side_effect = RuntimeError("S3 down")

        with pytest.raises(StorageError) as exc_info:
            storage.upload_file("key.mp4", b"data", "video/mp4")

        assert exc_info.value.operation == "upload"
        assert exc_info.value.key == "key.mp4"


class TestDownloadFile:
    """Verify download_file reads S3 object body and wraps errors."""

    def test_download_success(self, storage: StorageService, mock_s3: MagicMock):
        mock_body = MagicMock()
        mock_body.read.return_value = b"file-content"
        mock_s3.get_object.return_value = {"Body": mock_body}

        result = storage.download_file("videos/test.mp4")

        assert result == b"file-content"
        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="videos/test.mp4"
        )

    def test_download_wraps_s3_error(
        self, storage: StorageService, mock_s3: MagicMock
    ):
        mock_s3.get_object.side_effect = RuntimeError("Not found")

        with pytest.raises(StorageError) as exc_info:
            storage.download_file("missing.mp4")

        assert exc_info.value.operation == "download"
        assert exc_info.value.key == "missing.mp4"


class TestGeneratePresignedUrl:
    """Verify generate_presigned_url delegates correctly to S3 client."""

    def test_returns_presigned_url(self, storage: StorageService, mock_s3: MagicMock):
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/signed"

        url = storage.generate_presigned_url("videos/test.mp4", expires_in=600)

        assert url == "https://s3.example.com/signed"
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "videos/test.mp4"},
            ExpiresIn=600,
        )


class TestDeletePrefix:
    """Verify delete_prefix iterates paginator and deletes all objects."""

    def test_deletes_all_objects_across_pages(
        self, storage: StorageService, mock_s3: MagicMock
    ):
        page1 = {"Contents": [{"Key": "prefix/a.mp4"}, {"Key": "prefix/b.mp4"}]}
        page2 = {"Contents": [{"Key": "prefix/c.mp4"}]}

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [page1, page2]
        mock_s3.get_paginator.return_value = mock_paginator

        deleted = storage.delete_prefix("prefix/")

        assert deleted == 3
        assert mock_s3.delete_objects.call_count == 2
        mock_s3.get_paginator.assert_called_once_with("list_objects_v2")

    def test_empty_prefix_returns_zero(
        self, storage: StorageService, mock_s3: MagicMock
    ):
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Contents": []}]
        mock_s3.get_paginator.return_value = mock_paginator

        deleted = storage.delete_prefix("empty/")

        assert deleted == 0
        mock_s3.delete_objects.assert_not_called()


class TestBuildZipResponse:
    """Verify build_zip_response returns a StreamingResponse with correct headers."""

    def test_returns_streaming_response_with_zip_headers(
        self, storage: StorageService, mock_s3: MagicMock
    ):
        # Mock download_file for stream_zip
        mock_body = MagicMock()
        mock_body.read.return_value = b"video-bytes"
        mock_s3.get_object.return_value = {"Body": mock_body}

        response = storage.build_zip_response(
            [("videos/a.mp4", "video-001.mp4")],
            filename="export.zip",
        )

        assert isinstance(response, StreamingResponse)
        assert response.media_type == "application/zip"
        assert response.headers["content-disposition"] == 'attachment; filename="export.zip"'
