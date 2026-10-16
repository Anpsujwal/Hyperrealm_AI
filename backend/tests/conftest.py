"""
Shared test fixtures for HYPERREALM backend tests.

Uses an isolated in-memory store per test session — no cloud credentials needed.
"""
from __future__ import annotations

import asyncio
import os

# Ensure tests run with an isolated in-memory repository backend
os.environ["REPOSITORY_BACKEND"] = "memory"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.dependencies import init_repositories, get_user_repo
from backend.app.main import create_app
from backend.app.seed import seed_all


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def seeded_app():
    """FastAPI app with seed data loaded once per session."""
    init_repositories("memory")
    await seed_all()
    return create_app()


@pytest_asyncio.fixture(scope="session")
async def client(seeded_app):
    """Async HTTPX client wired to the in-memory app."""
    async with AsyncClient(
        transport=ASGITransport(app=seeded_app),
        base_url="http://test",
    ) as c:
        yield c


# ── Auth helpers ──────────────────────────────────────────────────────────────

async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture(scope="session")
async def alice_token(client):
    return await _login(client, "alice.chen@hyperrealm.io")


@pytest_asyncio.fixture(scope="session")
async def bob_token(client):
    return await _login(client, "bob.harris@hyperrealm.io")


@pytest_asyncio.fixture(scope="session")
async def carol_token(client):
    return await _login(client, "carol.adams@hyperrealm.io")


@pytest_asyncio.fixture(scope="session")
async def eve_token(client):
    return await _login(client, "eve.russo@hyperrealm.io")


def auth(token: str) -> dict:
    """Helper to build Authorization header."""
    return {"Authorization": f"Bearer {token}"}
