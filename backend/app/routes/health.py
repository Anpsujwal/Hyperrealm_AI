"""
Health-check endpoint.
Returns service status, version, and environment — no authentication required.
"""
from __future__ import annotations

import platform
import sys
from datetime import datetime

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Service health check")
async def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "repository_backend": settings.REPOSITORY_BACKEND,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python": sys.version,
        "platform": platform.system(),
    }


@router.get("/ping", summary="Liveness probe")
async def ping() -> dict:
    return {"pong": True}


@router.get("/integrations", summary="Live Cloud Integrations Status")
async def integrations_status() -> dict:
    """
    Returns explicit verification status for all 6 Google Cloud integrations:
    - Gemini / Vertex AI
    - Cloud Storage (GCS vs Local)
    - Document AI Layout Parser
    - Vertex AI Search / Discovery Engine
    - Google Calendar & Meet
    - Firestore & Data Persistence
    """
    from ..config import get_settings
    from ..agents.adk_runtime import get_gemini_runtime_status
    from ..services.storage import get_storage_service
    from ..services.document_ai import DocumentAIService
    from ..services.vertex_search import VertexAISearchService
    from ..services.calendar_service import get_calendar_service

    settings = get_settings()
    gemini_status = get_gemini_runtime_status()
    storage_svc = get_storage_service()
    storage_status = storage_svc.check_status() if hasattr(storage_svc, "check_status") else {"backend": settings.STORAGE_BACKEND}
    doc_ai_status = DocumentAIService().check_status()
    vertex_search_status = VertexAISearchService().check_status()
    calendar_status = get_calendar_service().check_status()
    firestore_status = {
        "enabled": settings.use_firestore,
        "database_id": settings.FIRESTORE_DATABASE_ID,
        "backend": settings.REPOSITORY_BACKEND,
        "status": "configured" if settings.use_firestore else "disabled",
    }

    return {
        "status": "ok",
        "app_mode": settings.APP_MODE,
        "integrations": {
            "gemini": gemini_status,
            "cloud_storage": storage_status,
            "document_ai": doc_ai_status,
            "vertex_ai_search": vertex_search_status,
            "google_calendar": calendar_status,
            "firestore": firestore_status,
        },
    }
