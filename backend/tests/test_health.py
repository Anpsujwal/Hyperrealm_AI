"""Tests for health-check endpoints."""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "repository_backend" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_ping(client):
    resp = await client.get("/health/ping")
    assert resp.status_code == 200
    assert resp.json() == {"pong": True}
