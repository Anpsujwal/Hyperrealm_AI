"""Tests for role-based access control."""
import pytest

from .conftest import auth


# ─── Admin-only: user list ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_can_list_users(client, alice_token):
    resp = await client.get("/api/v1/users", headers=auth(alice_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 10  # at least our 10 seed users


@pytest.mark.asyncio
async def test_non_admin_cannot_list_users(client, carol_token):
    """Software Developer should get 403 on admin-only list endpoint."""
    resp = await client.get("/api/v1/users", headers=auth(carol_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_list_users(client):
    resp = await client.get("/api/v1/users")
    assert resp.status_code == 401


# ─── Admin-only: audit logs ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_can_read_audit_logs(client, alice_token):
    resp = await client.get("/api/v1/admin/audit", headers=auth(alice_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_non_admin_cannot_read_audit_logs(client, eve_token):
    """QA Engineer should be denied audit log access."""
    resp = await client.get("/api/v1/admin/audit", headers=auth(eve_token))
    assert resp.status_code == 403


# ─── Lead-or-above: create guideline ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_technical_lead_can_create_guideline(client, bob_token):
    resp = await client.post(
        "/api/v1/guidelines",
        json={
            "title": "New Testing Guideline",
            "content": "All tests must be deterministic.",
            "category": "quality",
        },
        headers=auth(bob_token),
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_qa_engineer_cannot_create_guideline(client, eve_token):
    resp = await client.post(
        "/api/v1/guidelines",
        json={
            "title": "Sneaky Guideline",
            "content": "Not allowed.",
            "category": "security",
        },
        headers=auth(eve_token),
    )
    assert resp.status_code == 403


# ─── Role cannot be escalated by client ───────────────────────────────────────

@pytest.mark.asyncio
async def test_signup_cannot_claim_admin_role(client):
    """Even if the client sends role=admin in signup, they get EMPLOYEE."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "evil@hyperrealm.io",
            "name": "Evil User",
            "password": "Password123!",
            "role": "admin",  # This should be IGNORED
        },
    )
    assert resp.status_code == 201
    assert resp.json()["user"]["role"] == "employee"


# ─── Conversation ownership ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_cannot_access_another_users_conversation(client, carol_token, bob_token):
    """Carol creates a conversation; Bob should not be able to read it."""
    # Carol creates
    create_resp = await client.post(
        "/api/v1/conversations",
        json={"title": "Carol's private chat"},
        headers=auth(carol_token),
    )
    assert create_resp.status_code == 201
    conv_id = create_resp.json()["id"]

    # Bob tries to read
    read_resp = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers=auth(bob_token),
    )
    assert read_resp.status_code == 403


# ─── Approval resolution: only the designated approver ───────────────────────

@pytest.mark.asyncio
async def test_only_approver_can_resolve(client, carol_token, alice_token):
    """
    Carol submits an approval request designating Alice as approver.
    Carol herself should not be able to resolve it.
    """
    # Carol submits
    submit = await client.post(
        "/api/v1/approvals",
        json={
            "title": "Carol's request",
            "description": "test",
            "approver_id": "usr_alice",
        },
        headers=auth(carol_token),
    )
    assert submit.status_code == 201
    appr_id = submit.json()["id"]

    # Carol tries to resolve
    resolve = await client.post(
        f"/api/v1/approvals/{appr_id}/resolve",
        json={"status": "approved"},
        headers=auth(carol_token),
    )
    assert resolve.status_code == 403

    # Alice resolves — should succeed
    resolve_ok = await client.post(
        f"/api/v1/approvals/{appr_id}/resolve",
        json={"status": "approved", "decision_note": "Looks good"},
        headers=auth(alice_token),
    )
    assert resolve_ok.status_code == 200
    assert resolve_ok.json()["status"] == "approved"
