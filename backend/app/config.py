"""
HYPERREALM backend configuration.
Reads from environment variables / .env file at the project root.
All settings have safe defaults for local development.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

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

    # ── Operating Mode & AI Services (Phase 04) ──────────────────────────────
    # "demo" → local demo mode, seeded guidelines, local storage, deterministic mocks
    # "live" → Google Vertex AI, Google ADK, Cloud Storage, Vertex AI Search
    APP_MODE: Literal["demo", "live"] = "demo"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_FALLBACK_MODEL: str = "gemini-2.0-flash"
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GOOGLE_GENAI_USE_VERTEXAI: bool = True
    GEMINI_API_KEY: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    VERTEX_AI_SEARCH_DATA_STORE_ID: str = ""
    GCS_BUCKET_NAME: str = ""
    STORAGE_LOCAL_DIR: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "uploads")
    )

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
    def use_firestore(self) -> bool:
        return self.REPOSITORY_BACKEND == "firestore"

    def validate_cloud_configuration(self) -> dict[str, Any]:
        """Validate credentials and return configuration diagnostic report."""
        has_gcp_project = bool(self.GOOGLE_CLOUD_PROJECT or self.GCP_PROJECT_ID)
        has_gemini_api_key = bool(self.GEMINI_API_KEY)
        has_creds = bool(
            self.GOOGLE_APPLICATION_CREDENTIALS
            or self.FIREBASE_CREDENTIALS_PATH
            or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            or has_gemini_api_key
        )
        has_vertex_search = bool(self.VERTEX_AI_SEARCH_DATA_STORE_ID)
        has_gcs = bool(self.GCS_BUCKET_NAME)

        is_live_ready = (has_gcp_project and has_creds) or has_gemini_api_key

        return {
            "app_mode": self.APP_MODE,
            "configured_model": self.GEMINI_MODEL,
            "fallback_model": self.GEMINI_FALLBACK_MODEL,
            "is_live_ready": is_live_ready,
            "has_gcp_project": has_gcp_project,
            "has_credentials": has_creds,
            "has_vertex_search": has_vertex_search,
            "has_gcs": has_gcs,
            "local_storage_dir": self.STORAGE_LOCAL_DIR,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


settings = get_settings()
