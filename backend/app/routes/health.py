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
