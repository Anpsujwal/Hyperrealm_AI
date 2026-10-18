"""
HYPERREALM backend configuration.
Reads from environment variables / .env file at the project root.
All settings have safe defaults for local development.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _apply_test_overrides(self):
        import sys
        if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST"):
            self.APP_MODE = "demo"
            self.STORAGE_BACKEND = "local"
        return self

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "HYPERREALM API"
    APP_VERSION: str = "0.2.0"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:3000",
    ]

    # ── Auth / JWT (used in dev; prod uses Firebase identity tokens) ──────────
    JWT_SECRET: str = "CHANGE_ME_IN_PRODUCTION_use_256_bit_random_value"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # ── Firebase / Firestore ──────────────────────────────────────────────────
    # Leave empty to fall back to the in-memory dev repository.
    FIREBASE_CREDENTIALS_PATH: str = ""
    GCP_PROJECT_ID: str = ""

    # ── Repository adapter ────────────────────────────────────────────────────
    # "sqlite"    → persistent local database (hyperrealm.db)
    # "memory"    → fast ephemeral in-memory dev / test store
    # "firestore" → real Firestore (requires FIREBASE_CREDENTIALS_PATH)
    REPOSITORY_BACKEND: Literal["sqlite", "memory", "firestore"] = "sqlite"
    SQLITE_DB_PATH: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "hyperrealm.db")
    )

    # ── Operating Mode & AI Services ─────────────────────────────────────────
    # "demo" → local demo mode, seeded guidelines, local storage, deterministic mocks
    # "live" → Google Vertex AI, Google ADK, Cloud Storage, Vertex AI Search
    APP_MODE: Literal["demo", "live"] = "demo"
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_FALLBACK_MODEL: str = "gemini-2.5-flash"
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "global"
    GOOGLE_GENAI_USE_VERTEXAI: bool = True
    GEMINI_API_KEY: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # ── Google Cloud Storage & Document Storage ───────────────────────────────
    STORAGE_BACKEND: Literal["local", "gcs"] = "local"
    GCS_BUCKET_NAME: str = ""
    LOCAL_UPLOAD_DIR: str = "backend/uploads"
    STORAGE_LOCAL_DIR: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "uploads")
    )
    MAX_UPLOAD_SIZE_MB: int = 20
    RAG_TOP_K: int = 5

    # ── Vertex AI Search ──────────────────────────────────────────────────────
    VERTEX_AI_SEARCH_ENABLED: bool = False
    VERTEX_AI_SEARCH_LOCATION: str = "global"
    VERTEX_AI_SEARCH_DATA_STORE_ID: str = ""
    VERTEX_AI_SEARCH_ENGINE_ID: str = ""

    # ── Document AI ───────────────────────────────────────────────────────────
    DOCUMENT_AI_ENABLED: bool = False
    DOCUMENT_AI_LOCATION: str = "eu"
    DOCUMENT_AI_PROCESSOR_ID: str = ""

    # ── Firestore ─────────────────────────────────────────────────────────────
    FIRESTORE_ENABLED: bool = False
    FIRESTORE_DATABASE_ID: str = "(default)"

    # ── Google Calendar & Meet OAuth ──────────────────────────────────────────
    GOOGLE_CALENDAR_ENABLED: bool = False
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # ── Security & Secrets ────────────────────────────────────────────────────
    APP_SECRET_KEY: str = ""

    # ── Pagination ────────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_demo(self) -> bool:
        return self.APP_MODE == "demo"

    @property
    def is_live(self) -> bool:
        return self.APP_MODE == "live"

    @property
    def effective_jwt_secret(self) -> str:
        return self.APP_SECRET_KEY or self.JWT_SECRET

    @property
    def use_firestore(self) -> bool:
        return self.FIRESTORE_ENABLED or self.REPOSITORY_BACKEND == "firestore"

    def validate_cloud_configuration(self) -> dict[str, Any]:
        """Validate credentials and return detailed diagnostic report across all integrations."""
        has_gcp_project = bool(self.GOOGLE_CLOUD_PROJECT or self.GCP_PROJECT_ID)
        has_gemini_api_key = bool(self.GEMINI_API_KEY)
        has_creds = bool(
            self.GOOGLE_APPLICATION_CREDENTIALS
            or self.FIREBASE_CREDENTIALS_PATH
            or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            or has_gemini_api_key
        )
        has_vertex_search = bool(
            self.VERTEX_AI_SEARCH_ENABLED and (self.VERTEX_AI_SEARCH_DATA_STORE_ID or self.VERTEX_AI_SEARCH_ENGINE_ID)
        )
        has_doc_ai = bool(
            self.DOCUMENT_AI_ENABLED and self.DOCUMENT_AI_PROCESSOR_ID
        )
        has_gcs = bool(self.GCS_BUCKET_NAME)
        has_calendar = bool(
            self.GOOGLE_CALENDAR_ENABLED and self.GOOGLE_OAUTH_CLIENT_ID and self.GOOGLE_OAUTH_CLIENT_SECRET
        )
        has_firestore = bool(self.FIRESTORE_ENABLED and has_gcp_project and has_creds)

        is_gemini_ready = (has_gcp_project and has_creds) or has_gemini_api_key

        return {
            "app_mode": self.APP_MODE,
            "configured_model": self.GEMINI_MODEL,
            "fallback_model": self.GEMINI_FALLBACK_MODEL,
            "local_storage_dir": self.STORAGE_LOCAL_DIR,
            "is_live_ready": is_gemini_ready,
            "has_gcp_project": has_gcp_project,
            "has_credentials": has_creds,
            "gemini": {
                "status": "ready" if is_gemini_ready else "unconfigured",
                "model": self.GEMINI_MODEL,
                "vertexai": self.GOOGLE_GENAI_USE_VERTEXAI,
                "project": self.GOOGLE_CLOUD_PROJECT,
                "location": self.GOOGLE_CLOUD_LOCATION,
            },
            "storage": {
                "backend": self.STORAGE_BACKEND,
                "bucket_configured": has_gcs,
                "bucket_name": self.GCS_BUCKET_NAME if has_gcs else None,
                "local_dir": self.STORAGE_LOCAL_DIR,
            },
            "document_ai": {
                "enabled": self.DOCUMENT_AI_ENABLED,
                "configured": has_doc_ai,
                "location": self.DOCUMENT_AI_LOCATION,
                "processor_id": self.DOCUMENT_AI_PROCESSOR_ID,
            },
            "vertex_ai_search": {
                "enabled": self.VERTEX_AI_SEARCH_ENABLED,
                "configured": has_vertex_search,
                "data_store_id": self.VERTEX_AI_SEARCH_DATA_STORE_ID,
                "engine_id": self.VERTEX_AI_SEARCH_ENGINE_ID,
                "location": self.VERTEX_AI_SEARCH_LOCATION,
            },
            "firestore": {
                "enabled": self.FIRESTORE_ENABLED,
                "configured": has_firestore,
                "database_id": self.FIRESTORE_DATABASE_ID,
            },
            "calendar": {
                "enabled": self.GOOGLE_CALENDAR_ENABLED,
                "configured": has_calendar,
                "calendar_id": self.GOOGLE_CALENDAR_ID,
                "oauth_client_id_configured": bool(self.GOOGLE_OAUTH_CLIENT_ID),
            },
            "security": {
                "app_secret_key_configured": bool(self.APP_SECRET_KEY),
                "is_strong_secret": len(self.APP_SECRET_KEY) >= 32 if self.APP_SECRET_KEY else False,
            },
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


settings = get_settings()
