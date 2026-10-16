"""Tests for authentication endpoints."""
import pytest

from .conftest import auth


@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice.chen@hyperrealm.io", "password": "Password123!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "alice.chen@hyperrealm.io"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice.chen@hyperrealm.io", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@hyperrealm.io", "password": "Password123!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client, alice_token):
    resp = await client.get("/api/v1/auth/me", headers=auth(alice_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alice.chen@hyperrealm.io"
    assert data["role"] == "admin"
    # hashed_password must never be exposed
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_bad_token(client):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_signup_new_user(client):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@hyperrealm.io",
            "name": "New User",
            "password": "SecurePass99!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    # Self-registered users always get EMPLOYEE role regardless of what they request
    assert data["user"]["role"] == "employee"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client):
    payload = {
        "email": "duplicate@hyperrealm.io",
        "name": "Dup User",
        "password": "Password123!",
    }
    first = await client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/signup", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_logout(client, carol_token):
    resp = await client.post("/api/v1/auth/logout", headers=auth(carol_token))
    assert resp.status_code == 204
