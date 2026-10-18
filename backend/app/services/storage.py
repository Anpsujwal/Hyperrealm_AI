"""
HYPERREALM Storage Service.
Provides provider-based file storage: Local storage for demo mode and
Google Cloud Storage (GCS) when live cloud credentials are configured.
"""
from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional

from ..config import get_settings


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


class LocalStorageAdapter(StorageAdapter):
    """Local disk storage for local demo mode."""

    def __init__(self, base_dir: Optional[str] = None):
        settings = get_settings()
        self.base_dir = os.path.abspath(base_dir or settings.STORAGE_LOCAL_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        safe_user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(safe_user_dir, exist_ok=True)
        # Avoid collisions
        dest_path = os.path.join(safe_user_dir, filename)
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        return dest_path

    async def read_file(self, file_path_or_uri: str) -> bytes:
        if not os.path.exists(file_path_or_uri):
            raise FileNotFoundError(f"File not found: {file_path_or_uri}")
        with open(file_path_or_uri, "rb") as f:
            return f.read()

    async def delete_file(self, file_path_or_uri: str) -> bool:
        if os.path.exists(file_path_or_uri):
            os.remove(file_path_or_uri)
            return True
        return False


class GoogleCloudStorageAdapter(StorageAdapter):
    """Google Cloud Storage adapter for live cloud deployment."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client()
            except Exception as e:
                raise RuntimeError(f"Google Cloud Storage client initialization failed: {e}")
        return self._client

    async def save_file(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        blob_path = f"users/{user_id}/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(file_bytes)
        return f"gs://{self.bucket_name}/{blob_path}"

    async def read_file(self, file_path_or_uri: str) -> bytes:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        clean_path = file_path_or_uri.replace(f"gs://{self.bucket_name}/", "")
        blob = bucket.blob(clean_path)
        return blob.download_as_bytes()

    async def delete_file(self, file_path_or_uri: str) -> bool:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        clean_path = file_path_or_uri.replace(f"gs://{self.bucket_name}/", "")
        blob = bucket.blob(clean_path)
        if blob.exists():
            blob.delete()
            return True
        return False


def get_storage_service() -> StorageAdapter:
    settings = get_settings()
    if settings.APP_MODE == "live" and settings.GCS_BUCKET_NAME:
        try:
            return GoogleCloudStorageAdapter(settings.GCS_BUCKET_NAME)
        except Exception:
            # Fall back safely to local storage if GCS not configured
            pass
    return LocalStorageAdapter(settings.STORAGE_LOCAL_DIR)
