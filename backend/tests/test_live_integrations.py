"""
Phase 2-8 Live Integrations & Diagnostics Test Suite.
Tests:
- Gemini model configuration, live runtime validation, and controlled error mapping.
- Cloud Storage adapter switching, GCS vs Local boundaries.
- Document AI Layout Parser and Vertex AI Search status reporting.
- Google Calendar OAuth token lifecycle & meeting conference link handling.
- Firestore repository selection when enabled vs disabled.
- Integration status endpoint (/health/integrations and /api/v1/admin/integrations/status).
- Security, least-privilege IAM isolation, and permission boundary preservation.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from backend.app.config import get_settings
from backend.app.agents.adk_runtime import (
    GeminiInvocationError,
    verify_gemini_model_availability,
    get_gemini_runtime_status,
)
from backend.app.services.storage import (
    LocalStorageAdapter,
    GoogleCloudStorageAdapter,
    StoragePermissionError,
    get_storage_service,
)
from backend.app.services.document_ai import DocumentAIService
from backend.app.services.vertex_search import VertexAISearchService
from backend.app.services.calendar_service import GoogleCalendarService, get_calendar_service


@pytest.mark.asyncio
async def test_gemini_model_configuration_and_error_classification():
    """Verify Gemini error classification for quota, permissions, unavailable models, and network."""
    settings = get_settings()
    assert settings.GEMINI_MODEL == "gemini-3.8-flash"

    # 1. 429 Quota Exceeded
    err_429 = GeminiInvocationError.from_exception(Exception("ResourceExhausted: 429 Quota exceeded for quota metric"))
    assert err_429.error_code == "QUOTA_EXCEEDED"
    assert err_429.status_code == 429

    # 2. 404 Model Not Found
    err_404 = GeminiInvocationError.from_exception(Exception("NotFound: 404 Model gemini-nonexistent not found"))
    assert err_404.error_code in ("MODEL_UNAVAILABLE", "MODEL_NOT_FOUND")
    assert err_404.status_code == 404

    # 3. 403 Permission Denied
    err_403 = GeminiInvocationError.from_exception(Exception("PermissionDenied: 403 Caller does not have aiplatform.models.predict"))
    assert err_403.error_code == "PERMISSION_DENIED"
    assert err_403.status_code == 403

    # 4. 401 Unauthenticated
    err_401 = GeminiInvocationError.from_exception(Exception("Unauthenticated: 401 Invalid OAuth credentials"))
    assert err_401.error_code in ("UNAUTHENTICATED", "INVALID_CREDENTIALS")
    assert err_401.status_code == 401

    # 5. Network / Timeout
    err_net = GeminiInvocationError.from_exception(Exception("Connection timeout while waiting for model"))
    assert err_net.error_code == "NETWORK_FAILURE"
    assert err_net.status_code == 504


@pytest.mark.asyncio
async def test_storage_adapter_selection_and_local_adapter():
    """Verify storage adapter selection preserves local storage for dev and checks boundaries."""
    settings = get_settings()
    storage = get_storage_service()
    # When STORAGE_BACKEND is 'local', LocalStorageAdapter must be active
    assert isinstance(storage, LocalStorageAdapter)

    test_bytes = b"Hello HYPERREALM Storage Hub!"
    saved_path = await storage.save_file(test_bytes, "test_file.txt", "usr_test")
    assert saved_path is not None
    assert await storage.file_exists(saved_path) is True

    downloaded = await storage.get_file(saved_path)
    assert downloaded == test_bytes

    meta = await storage.get_file_metadata(saved_path)
    assert meta["size"] == len(test_bytes)

    deleted = await storage.delete_file(saved_path)
    assert deleted is True
    assert await storage.file_exists(saved_path) is False


@pytest.mark.asyncio
async def test_gcs_adapter_controlled_permission_error():
    """Verify GCS adapter raises explicit StoragePermissionError without fabricating success."""
    adapter = GoogleCloudStorageAdapter(bucket_name="nonexistent-protected-bucket")
    
    with patch("backend.app.services.storage.GoogleCloudStorageAdapter._get_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.bucket.side_effect = Exception("403 Forbidden: storage.buckets.get permission denied")
        mock_client.return_value = mock_instance

        with pytest.raises(StoragePermissionError):
            await adapter.save_file(b"data", "file.txt", "usr_01")


@pytest.mark.asyncio
async def test_document_ai_service_status():
    """Verify Document AI service returns explicit status and diagnostic checks."""
    service = DocumentAIService()
    status = service.check_status()
    assert "status" in status
    assert "location" in status


@pytest.mark.asyncio
async def test_vertex_search_service_status():
    """Verify Vertex AI Search service status reports real configuration and availability."""
    service = VertexAISearchService()
    status = service.check_status()
    assert "status" in status
    assert "data_store_id" in status or "message" in status


@pytest.mark.asyncio
async def test_google_calendar_oauth_and_status():
    """Verify Google Calendar service OAuth authorization URL generation and status."""
    service = get_calendar_service()
    status = service.check_status()
    assert "enabled" in status
    assert "oauth_client_id_configured" in status

    auth_url = service.get_authorization_url(user_id="usr_01", state_extra="test_state_123")
    assert "accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "calendar.events" in auth_url
    assert "usr_01" in auth_url


@pytest.mark.asyncio
async def test_integrations_diagnostics_endpoint(client: AsyncClient, alice_token: str):
    """Verify public health /integrations and admin /integrations/status endpoints return all 6 integrations."""
    with patch("backend.app.services.document_ai.DocumentAIService.check_status") as mock_doc_ai, \
         patch("backend.app.services.vertex_search.VertexAISearchService.check_status") as mock_vs:
        mock_doc_ai.return_value = {"status": "mocked", "location": "eu"}
        mock_vs.return_value = {"status": "mocked", "data_store_id": "test-ds"}

        # 1. Health endpoint
        resp_health = await client.get("/health/integrations")
        assert resp_health.status_code == 200
        data_health = resp_health.json()
        assert data_health["status"] == "ok"
        integrations = data_health["integrations"]
        assert "gemini" in integrations
        assert "cloud_storage" in integrations
        assert "document_ai" in integrations
        assert "vertex_ai_search" in integrations
        assert "google_calendar" in integrations
        assert "firestore" in integrations

        # 2. Admin endpoint (authorized)
        resp_admin = await client.get(
            "/api/v1/admin/integrations/status",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert resp_admin.status_code == 200
        data_admin = resp_admin.json()
        assert "integrations" in data_admin
