"""
HYPERREALM backend configuration.
Reads from environment variables / .env file at the project root.
All settings have safe defaults for local development.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

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

    # ── Pagination ────────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def use_firestore(self) -> bool:
        return self.REPOSITORY_BACKEND == "firestore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
