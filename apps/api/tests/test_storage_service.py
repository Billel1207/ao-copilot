"""Tests for app.services.storage — S3 and LocalStorage services."""
import os
import uuid
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from botocore.exceptions import ClientError


# ---------------------------------------------------------------------------
# LocalStorageService
# ---------------------------------------------------------------------------

class TestLocalStorageService:
    def test_init_creates_directory(self, tmp_path):
        from app.services.storage import LocalStorageService
        base = str(tmp_path / "test-storage")
        svc = LocalStorageService(base_dir=base)
        assert Path(base).exists()

    def test_generate_s3_key(self, tmp_path):
        from app.services.storage import LocalStorageService
        svc = LocalStorageService(base_dir=str(tmp_path))
        key = svc.generate_s3_key("org-1", "proj-1", "document.pdf")
        assert key.startswith("orgs/org-1/projects/proj-1/docs/")
        assert key.endswith(".pdf")

    def test_generate_s3_key_no_extension(self, tmp_path):
        from app.services.storage import LocalStorageService
        svc = LocalStorageService(base_dir=str(tmp_path))
        key = svc.generate_s3_key("org-1", "proj-1", "noext")
        assert key.endswith(".pdf")  # default extension

    def test_upload_and_download(self, tmp_path):
        from app.services.storage import LocalStorageService
        svc = LocalStorageService(base_dir=str(tmp_path))
        key = "orgs/test/file.pdf"
        data = b"%PDF-1.4 test content"
        svc.upload_bytes(key, data)
        result = svc.download_bytes(key)
        assert result == data

    def test_delete_object(self, tmp_path):
        from app.services.storage import LocalStorageService
        svc = LocalStorageService(base_dir=str(tmp_path))
        key = "orgs/test/deleteme.pdf"
        svc.upload_bytes(key, b"data")
        svc.delete_object(key)
        assert not (tmp_path / key).exists()

    def test_delete_nonexistent_object(self, tmp_path):
        from app.services.storage import LocalStorageService
        svc = LocalStorageService(base_dir=str(tmp_path))
        # Should not raise
        svc.delete_object("nonexistent/key.pdf")

    def test_signed_download_url(self, tmp_path):
        from app.services.storage import LocalStorageService
        svc = LocalStorageService(base_dir=str(tmp_path))
        url = svc.get_signed_download_url("orgs/test/file.pdf")
        assert "/local-storage/" in url

    def test_signed_upload_url(self, tmp_path):
        from app.services.storage import LocalStorageService
        svc = LocalStorageService(base_dir=str(tmp_path))
        url = svc.get_signed_upload_url("orgs/test/file.pdf")
        assert "/local-storage/" in url


# ---------------------------------------------------------------------------
# StorageService (S3) — mocked boto3
# ---------------------------------------------------------------------------

class TestStorageService:
    @patch("app.services.storage.boto3")
    def test_generate_s3_key(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        key = svc.generate_s3_key("org-abc", "proj-xyz", "ccap.pdf")
        assert "orgs/org-abc/projects/proj-xyz/docs/" in key
        assert key.endswith(".pdf")

    @patch("app.services.storage.boto3")
    def test_upload_bytes(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = True
        mock_boto3.client.return_value = mock_client

        svc.upload_bytes("test/key.pdf", b"pdf-data", "application/pdf")
        mock_client.put_object.assert_called_once_with(
            Bucket=svc.bucket,
            Key="test/key.pdf",
            Body=b"pdf-data",
            ContentType="application/pdf",
        )

    @patch("app.services.storage.boto3")
    def test_download_bytes(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = True
        mock_body = MagicMock()
        mock_body.read.return_value = b"downloaded-content"
        mock_client.get_object.return_value = {"Body": mock_body}
        mock_boto3.client.return_value = mock_client

        result = svc.download_bytes("test/key.pdf")
        assert result == b"downloaded-content"

    @patch("app.services.storage.boto3")
    def test_delete_object(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = True
        mock_boto3.client.return_value = mock_client

        svc.delete_object("test/key.pdf")
        mock_client.delete_object.assert_called_once_with(
            Bucket=svc.bucket, Key="test/key.pdf"
        )

    @patch("app.services.storage.boto3")
    def test_get_signed_download_url(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = True
        mock_client.generate_presigned_url.return_value = "https://s3/signed/url"
        mock_boto3.client.return_value = mock_client

        url = svc.get_signed_download_url("test/key.pdf")
        assert url == "https://s3/signed/url"
        mock_client.generate_presigned_url.assert_called_once()

    @patch("app.services.storage.boto3")
    def test_get_signed_upload_url(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = True
        mock_client.generate_presigned_url.return_value = "https://s3/upload/url"
        mock_boto3.client.return_value = mock_client

        url = svc.get_signed_upload_url("test/key.pdf", "application/pdf")
        assert url == "https://s3/upload/url"

    @patch("app.services.storage.boto3")
    def test_ensure_bucket_creates_if_not_exists(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadBucket"
        )
        mock_boto3.client.return_value = mock_client

        svc._get_client()
        mock_client.create_bucket.assert_called_once()

    @patch("app.services.storage.boto3")
    def test_ensure_bucket_raises_on_other_error(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "403"}}, "HeadBucket"
        )
        mock_boto3.client.return_value = mock_client

        with pytest.raises(ClientError):
            svc._get_client()

    @patch("app.services.storage.boto3")
    def test_lazy_init_only_once(self, mock_boto3):
        from app.services.storage import StorageService
        svc = StorageService()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = True
        mock_boto3.client.return_value = mock_client

        svc._get_client()
        svc._get_client()
        # boto3.client should only be called once (lazy init)
        assert mock_boto3.client.call_count == 1
