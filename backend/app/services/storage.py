"""
HYPERREALM Storage Service.
Provides provider-based file storage: Local disk storage for development/testing
and Google Cloud Storage (GCS) when configured.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..config import get_settings

logger = logging.getLogger("hyperrealm.storage")


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class StoragePermissionError(StorageError):
    """Raised when GCS returns 403 Forbidden or IAM permission is denied."""
    pass


class StorageNotFoundError(StorageError):
    """Raised when file or bucket does not exist."""
    pass


class StorageAdapter(ABC):
    @abstractmethod
    async def save_file(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        """Save file bytes and return access URI or local path."""
        ...

    @abstractmethod
    async def read_file(self, file_path_or_uri: str) -> bytes:
        """Read and return file bytes."""
        ...

    @abstractmethod
    async def delete_file(self, file_path_or_uri: str) -> bool:
        """Delete file if it exists."""
        ...

    @abstractmethod
    async def exists(self, file_path_or_uri: str) -> bool:
        """Check if file exists."""
        ...

    @abstractmethod
    async def get_metadata(self, file_path_or_uri: str) -> dict[str, Any]:
        """Get file metadata (size, content_type, updated_at)."""
        ...

    async def get_file(self, file_path_or_uri: str) -> bytes:
        return await self.read_file(file_path_or_uri)

    async def file_exists(self, file_path_or_uri: str) -> bool:
        return await self.exists(file_path_or_uri)

    async def get_file_metadata(self, file_path_or_uri: str) -> dict[str, Any]:
        meta = await self.get_metadata(file_path_or_uri)
        if "size" not in meta and "size_bytes" in meta:
            meta["size"] = meta["size_bytes"]
        return meta


class LocalStorageAdapter(StorageAdapter):
    """Local disk storage for development and offline testing."""

    def __init__(self, base_dir: Optional[str] = None):
        settings = get_settings()
        self.base_dir = os.path.abspath(base_dir or settings.STORAGE_LOCAL_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        safe_user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(safe_user_dir, exist_ok=True)
        dest_path = os.path.join(safe_user_dir, filename)
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        return dest_path

    async def read_file(self, file_path_or_uri: str) -> bytes:
        if not os.path.exists(file_path_or_uri):
            raise StorageNotFoundError(f"File not found on local disk: {file_path_or_uri}")
        with open(file_path_or_uri, "rb") as f:
            return f.read()

    async def delete_file(self, file_path_or_uri: str) -> bool:
        if os.path.exists(file_path_or_uri):
            os.remove(file_path_or_uri)
            return True
        return False

    async def exists(self, file_path_or_uri: str) -> bool:
        return os.path.exists(file_path_or_uri)

    async def get_metadata(self, file_path_or_uri: str) -> dict[str, Any]:
        if not os.path.exists(file_path_or_uri):
            raise StorageNotFoundError(f"File not found: {file_path_or_uri}")
        st = os.stat(file_path_or_uri)
        return {
            "size_bytes": st.st_size,
            "modified_time": st.st_mtime,
            "provider": "local",
            "path": file_path_or_uri,
        }


class GoogleCloudStorageAdapter(StorageAdapter):
    """Google Cloud Storage adapter for live cloud deployment."""

    def __init__(self, bucket_name: str):
        if not bucket_name:
            raise StorageError("GCS_BUCKET_NAME is not configured.")
        self.bucket_name = bucket_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            settings = get_settings()
            if settings.GOOGLE_APPLICATION_CREDENTIALS and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
            try:
                from google.cloud import storage
                creds_file = settings.GOOGLE_APPLICATION_CREDENTIALS
                if creds_file and os.path.isfile(creds_file):
                    self._client = storage.Client.from_service_account_json(
                        creds_file,
                        project=settings.GOOGLE_CLOUD_PROJECT or None,
                    )
                else:
                    self._client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT or None)
            except Exception as e:
                raise StorageError(f"Google Cloud Storage client initialization failed: {e}") from e
        return self._client

    def _map_gcs_exception(self, exc: Exception, action: str) -> Exception:
        err_msg = str(exc)
        if "403" in err_msg or "Forbidden" in exc.__class__.__name__:
            return StoragePermissionError(
                f"Google Cloud Storage access denied during {action} on bucket '{self.bucket_name}'. "
                f"Ensure the service account has 'Storage Object Admin' (roles/storage.objectAdmin) role. Original: {exc}"
            )
        if "404" in err_msg or "NotFound" in exc.__class__.__name__:
            return StorageNotFoundError(
                f"Google Cloud Storage resource not found during {action} on bucket '{self.bucket_name}': {exc}"
            )
        return StorageError(f"Google Cloud Storage {action} failed: {exc}")

    async def save_file(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        client = self._get_client()
        blob_path = f"users/{user_id}/{filename}"
        
        def _upload():
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(blob_path)
                blob.upload_from_string(file_bytes)
                return f"gs://{self.bucket_name}/{blob_path}"
            except Exception as exc:
                raise self._map_gcs_exception(exc, f"uploading '{filename}'") from exc

        return await asyncio.to_thread(_upload)

    async def read_file(self, file_path_or_uri: str) -> bytes:
        client = self._get_client()
        clean_path = file_path_or_uri.replace(f"gs://{self.bucket_name}/", "")

        def _download():
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(clean_path)
                return blob.download_as_bytes()
            except Exception as exc:
                raise self._map_gcs_exception(exc, f"reading '{clean_path}'") from exc

        return await asyncio.to_thread(_download)

    async def delete_file(self, file_path_or_uri: str) -> bool:
        client = self._get_client()
        clean_path = file_path_or_uri.replace(f"gs://{self.bucket_name}/", "")

        def _delete():
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(clean_path)
                if blob.exists():
                    blob.delete()
                    return True
                return False
            except Exception as exc:
                raise self._map_gcs_exception(exc, f"deleting '{clean_path}'") from exc

        return await asyncio.to_thread(_delete)

    async def exists(self, file_path_or_uri: str) -> bool:
        client = self._get_client()
        clean_path = file_path_or_uri.replace(f"gs://{self.bucket_name}/", "")

        def _check():
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(clean_path)
                return blob.exists()
            except Exception as exc:
                raise self._map_gcs_exception(exc, f"checking existence of '{clean_path}'") from exc

        return await asyncio.to_thread(_check)

    async def get_metadata(self, file_path_or_uri: str) -> dict[str, Any]:
        client = self._get_client()
        clean_path = file_path_or_uri.replace(f"gs://{self.bucket_name}/", "")

        def _meta():
            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.get_blob(clean_path)
                if not blob:
                    raise StorageNotFoundError(f"Blob '{clean_path}' not found in bucket '{self.bucket_name}'.")
                return {
                    "size_bytes": blob.size,
                    "content_type": blob.content_type,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "provider": "gcs",
                    "uri": f"gs://{self.bucket_name}/{clean_path}",
                }
            except Exception as exc:
                raise self._map_gcs_exception(exc, f"fetching metadata for '{clean_path}'") from exc

        return await asyncio.to_thread(_meta)


def get_storage_service() -> StorageAdapter:
    """Return configured storage provider based on STORAGE_BACKEND setting."""
    settings = get_settings()
    if settings.STORAGE_BACKEND == "gcs":
        return GoogleCloudStorageAdapter(settings.GCS_BUCKET_NAME)
    return LocalStorageAdapter(settings.STORAGE_LOCAL_DIR)


async def check_storage_status() -> dict[str, Any]:
    """Diagnostic check verifying storage provider connectivity and permissions."""
    settings = get_settings()
    if settings.STORAGE_BACKEND == "gcs":
        if not settings.GCS_BUCKET_NAME:
            return {
                "backend": "gcs",
                "status": "unconfigured",
                "message": "STORAGE_BACKEND is set to 'gcs' but GCS_BUCKET_NAME is empty.",
            }
        try:
            adapter = GoogleCloudStorageAdapter(settings.GCS_BUCKET_NAME)
            client = adapter._get_client()
            # Test bucket get
            await asyncio.to_thread(client.get_bucket, settings.GCS_BUCKET_NAME)
            return {
                "backend": "gcs",
                "status": "operational",
                "bucket": settings.GCS_BUCKET_NAME,
                "message": f"Connected to GCS bucket '{settings.GCS_BUCKET_NAME}'.",
            }
        except Exception as exc:
            return {
                "backend": "gcs",
                "status": "permission_denied" if "403" in str(exc) else "error",
                "bucket": settings.GCS_BUCKET_NAME,
                "error": str(exc),
                "message": f"GCS bucket check failed: {exc}",
            }
    else:
        local_dir = settings.STORAGE_LOCAL_DIR
        exists = os.path.exists(local_dir)
        writable = os.access(local_dir, os.W_OK) if exists else False
        return {
            "backend": "local",
            "status": "operational" if (exists and writable) else "error",
            "local_dir": local_dir,
            "message": f"Local storage active at '{local_dir}'.",
        }
