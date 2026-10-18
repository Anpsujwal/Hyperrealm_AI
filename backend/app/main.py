"""
HYPERREALM FastAPI application factory.
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .dependencies import init_repositories

logger = logging.getLogger("hyperrealm")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init repos + seed data on startup."""
    settings = get_settings()
    logger.info("Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)

    init_repositories()
    logger.info("Repositories initialised")

    if settings.is_dev or os.environ.get("AUTO_SEED", "true").lower() in ("true", "1"):
        from .seed import seed_all
        await seed_all()
        logger.info("Seed data loaded")

    yield

    logger.info("Shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "HYPERREALM enterprise AI workspace API. "
            "Phase 02 — data layer and authentication."
        ),
        docs_url="/docs" if settings.is_dev else None,
        redoc_url="/redoc" if settings.is_dev else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handlers ─────────────────────────────────────────────

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "internal_error",
                "message": "An unexpected error occurred",
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    from .routes.health import router as health_router
    from .routes.auth import router as auth_router
    from .routes.users import router as users_router
    from .routes.conversations import router as conv_router
    from .routes.tasks import router as tasks_router
    from .routes.meetings import router as meetings_router
    from .routes.knowledge import router as knowledge_router
    from .routes.learning import router as learning_router
    from .routes.incidents import router as incidents_router
    from .routes.notifications import router as notif_router
    from .routes.admin import router as admin_router
    from .routes.chat import router as chat_router
    from .routes.actions import router as actions_router
    from .routes.onboarding import router as onboarding_router

    api_prefix = "/api/v1"

    app.include_router(health_router)
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(users_router, prefix=api_prefix)
    app.include_router(conv_router, prefix=api_prefix)
    app.include_router(tasks_router, prefix=api_prefix)
    app.include_router(meetings_router, prefix=api_prefix)
    app.include_router(knowledge_router, prefix=api_prefix)
    app.include_router(knowledge_router, prefix=f"{api_prefix}/knowledge")
    app.include_router(learning_router, prefix=api_prefix)
    app.include_router(onboarding_router, prefix=api_prefix)
    app.include_router(incidents_router, prefix=api_prefix)
    app.include_router(notif_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)
    app.include_router(chat_router, prefix=api_prefix)
    app.include_router(actions_router, prefix=api_prefix)

    # ── Frontend static assets (Production SPA) ──────────────────────────────
    dist_candidates = [
        os.environ.get("FRONTEND_DIST", ""),
        "/app/frontend/dist",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    ]
    frontend_dist = next((p for p in dist_candidates if p and os.path.isdir(p)), None)

    if frontend_dist and (settings.APP_ENV == "production" or os.environ.get("SERVE_FRONTEND", "").lower() in ("true", "1")):
        from fastapi.staticfiles import StaticFiles
        from starlette.exceptions import HTTPException as StarletteHTTPException

        class SPAStaticFiles(StaticFiles):
            async def get_response(self, path: str, scope):
                try:
                    return await super().get_response(path, scope)
                except (HTTPException, StarletteHTTPException) as exc:
                    if exc.status_code == 404:
                        norm = path.replace(os.sep, "/").lstrip("/")
                        if norm.startswith("api/") or norm.startswith("health") or norm.startswith("docs") or norm == "openapi.json":
                            raise
                        return await super().get_response("index.html", scope)
                    raise

        app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="spa")

    return app


# Module-level app instance for uvicorn
app = create_app()
