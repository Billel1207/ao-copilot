import os
import uuid
import structlog
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError

from app.config import settings

logger = structlog.get_logger(__name__)


class LocalStorageService:
    """Fallback filesystem storage for local dev when S3/MinIO is unavailable."""

    def __init__(self, base_dir: str | None = None):
        self.base = Path(base_dir or os.path.join(os.getcwd(), ".local-storage"))
        self.base.mkdir(parents=True, exist_ok=True)
        logger.info("LocalStorageService activated — files stored in %s", self.base)

    def generate_s3_key(self, org_id: str, project_id: str, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
        return f"orgs/{org_id}/projects/{project_id}/docs/{uuid.uuid4()}.{ext}"

    def upload_bytes(self, s3_key: str, data: bytes, content_type: str = "application/pdf") -> None:
        path = self.base / s3_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def download_bytes(self, s3_key: str) -> bytes:
        return (self.base / s3_key).read_bytes()

    def delete_object(self, s3_key: str) -> None:
        path = self.base / s3_key
        if path.exists():
            path.unlink()

    def get_signed_download_url(self, s3_key: str) -> str:
        return f"/local-storage/{s3_key}"

    def get_signed_upload_url(self, s3_key: str, content_type: str = "application/pdf") -> str:
        return f"/local-storage/{s3_key}"


class StorageService:
    def __init__(self):
        self._client = None
        self.bucket = settings.S3_BUCKET_NAME

    def _get_client(self):
        """Lazy init du client S3 — connexion différée à la première utilisation."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=Config(signature_version="s3v4"),
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self):
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("404", "NoSuchBucket"):
                self._client.create_bucket(Bucket=self.bucket)
                logger.info(f"Bucket MinIO créé : {self.bucket}")
            else:
                raise

    def generate_s3_key(self, org_id: str, project_id: str, filename: str) -> str:
        """Génère une clé S3 avec UUID — jamais le nom original."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
        return f"orgs/{org_id}/projects/{project_id}/docs/{uuid.uuid4()}.{ext}"

    def get_signed_upload_url(self, s3_key: str, content_type: str = "application/pdf") -> str:
        """URL présignée pour upload direct depuis le frontend."""
        return self._get_client().generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": s3_key, "ContentType": content_type},
            ExpiresIn=600,
        )

    def get_signed_download_url(self, s3_key: str) -> str:
        """URL présignée pour téléchargement — 15 minutes."""
        return self._get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=settings.S3_SIGNED_URL_EXPIRY,
        )

    def upload_bytes(self, s3_key: str, data: bytes, content_type: str = "application/pdf") -> None:
        self._get_client().put_object(
            Bucket=self.bucket, Key=s3_key, Body=data, ContentType=content_type
        )

    def download_bytes(self, s3_key: str) -> bytes:
        response = self._get_client().get_object(Bucket=self.bucket, Key=s3_key)
        return response["Body"].read()

    def delete_object(self, s3_key: str) -> None:
        self._get_client().delete_object(Bucket=self.bucket, Key=s3_key)


def _create_storage_service() -> StorageService | LocalStorageService:
    """Try S3, fall back to local filesystem if unreachable."""
    try:
        svc = StorageService()
        svc._get_client()
        logger.info("S3 storage connected (%s)", settings.S3_ENDPOINT_URL)
        return svc
    except (EndpointConnectionError, ClientError, NoCredentialsError, Exception) as e:
        logger.warning("S3 unavailable (%s) — falling back to local storage", e)
        return LocalStorageService()


storage_service = _create_storage_service()
