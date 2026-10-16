"""Tests for core data creation and retrieval."""
import pytest

from .conftest import auth


# ─── Users ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_user_by_id(client, alice_token):
    resp = await client.get("/api/v1/users/usr_bob", headers=auth(alice_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "usr_bob"
    assert data["name"] == "Bob Harris"
    assert data["role"] == "technical_lead"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_user_not_found(client, alice_token):
    resp = await client.get("/api/v1/users/usr_nonexistent", headers=auth(alice_token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_org_tree(client, carol_token):
    resp = await client.get("/api/v1/users/org/tree", headers=auth(carol_token))
    assert resp.status_code == 200
    tree = resp.json()
    assert isinstance(tree, list)
    # Root should be Alice (no manager)
    assert any(node["user"]["id"] == "usr_alice" for node in tree)


@pytest.mark.asyncio
async def test_direct_reports(client, alice_token):
    resp = await client.get("/api/v1/users/usr_alice/reports", headers=auth(alice_token))
    assert resp.status_code == 200
    reports = resp.json()
    report_ids = [u["id"] for u in reports]
    assert "usr_bob" in report_ids
    assert "usr_frank" in report_ids
    assert "usr_henry" in report_ids


# ─── Tasks ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_get_task(client, bob_token):
    create_resp = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Test task from test suite",
            "description": "Automated test task",
            "priority": "high",
            "assignee_id": "usr_carol",
            "project_id": "proj_phoenix",
        },
        headers=auth(bob_token),
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    assert task["title"] == "Test task from test suite"
    assert task["reporter_id"] == "usr_bob"
    assert task["status"] == "todo"

    # Retrieve by ID
    get_resp = await client.get(f"/api/v1/tasks/{task['id']}", headers=auth(bob_token))
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == task["id"]


@pytest.mark.asyncio
async def test_list_tasks_paginated(client, carol_token):
    resp = await client.get(
        "/api/v1/tasks?page=1&page_size=5",
        headers=auth(carol_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "has_next" in data
    assert len(data["items"]) <= 5


@pytest.mark.asyncio
async def test_update_task_status(client, bob_token):
    # Create
    create = await client.post(
        "/api/v1/tasks",
        json={"title": "Status update test", "priority": "medium"},
        headers=auth(bob_token),
    )
    task_id = create.json()["id"]

    # Update
    update = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=auth(bob_token),
    )
    assert update.status_code == 200
    assert update.json()["status"] == "in_progress"


# ─── Conversations ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_conversation_and_add_messages(client, carol_token):
    # Create conversation
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={"title": "Test chat", "agent_id": "knowledge"},
        headers=auth(carol_token),
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # Add a user message
    msg_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "user", "content": "Hello, what is the remote work policy?"},
        headers=auth(carol_token),
    )
    assert msg_resp.status_code == 201
    assert msg_resp.json()["role"] == "user"

    # Add an assistant message
    asst_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "assistant", "content": "The remote work policy is...", "agent_id": "knowledge"},
        headers=auth(carol_token),
    )
    assert asst_resp.status_code == 201

    # List messages
    list_resp = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth(carol_token),
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 2


# ─── Meetings ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_meetings(client, bob_token):
    create_resp = await client.post(
        "/api/v1/meetings",
        json={
            "title": "Backend Design Review",
            "type": "general",
            "scheduled_at": "2026-10-20T14:00:00",
            "duration_minutes": 60,
            "attendee_ids": ["usr_carol", "usr_david"],
        },
        headers=auth(bob_token),
    )
    assert create_resp.status_code == 201
    meeting = create_resp.json()
    assert meeting["organiser_id"] == "usr_bob"

    list_resp = await client.get("/api/v1/meetings", headers=auth(bob_token))
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1


# ─── Incidents ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_update_incident(client, carol_token):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Test incident",
            "description": "Error rate spiked unexpectedly",
            "severity": "P3",
        },
        headers=auth(carol_token),
    )
    assert create_resp.status_code == 201
    inc_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/v1/incidents/{inc_id}",
        json={"status": "investigating", "assignee_id": "usr_carol"},
        headers=auth(carol_token),
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "investigating"


# ─── Notifications ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_and_mark_notifications(client, alice_token):
    list_resp = await client.get("/api/v1/notifications", headers=auth(alice_token))
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 2  # Alice has 2 seeded notifications

    first_id = items[0]["id"]
    mark_resp = await client.post(
        f"/api/v1/notifications/{first_id}/read",
        headers=auth(alice_token),
    )
    assert mark_resp.status_code == 204


# ─── Knowledge hub ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_documents(client, carol_token):
    resp = await client.get("/api/v1/documents", headers=auth(carol_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3  # 3 seeded documents


@pytest.mark.asyncio
async def test_list_guidelines(client, carol_token):
    resp = await client.get("/api/v1/guidelines", headers=auth(carol_token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 3


# ─── Learning ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_learning_resources(client, carol_token):
    resp = await client.get("/api/v1/learning/resources", headers=auth(carol_token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 6


@pytest.mark.asyncio
async def test_learning_progress_upsert(client, carol_token):
    resp = await client.put(
        "/api/v1/learning/resources/learn_fastapi/progress",
        json={"status": "completed", "progress_pct": 100},
        headers=auth(carol_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["progress_pct"] == 100


@pytest.mark.asyncio
async def test_my_learning_progress(client, carol_token):
    resp = await client.get("/api/v1/learning/progress/me", headers=auth(carol_token))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 3  # Carol has 3 seeded progress entries


# ─── Admin ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_departments(client, carol_token):
    resp = await client.get("/api/v1/admin/departments", headers=auth(carol_token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 2


@pytest.mark.asyncio
async def test_list_projects(client, bob_token):
    resp = await client.get("/api/v1/admin/projects", headers=auth(bob_token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 2
