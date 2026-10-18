"""
Tests for meeting invitations, RSVPs, automatic rescheduling,
and calendar API collision detection.
"""
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_meeting_schedule_sends_notification_to_attendee(client: AsyncClient, bob_token: str, carol_token: str):
    # Bob schedules a meeting with Carol
    meet_time = "2026-11-01T10:00:00"
    create_resp = await client.post(
        "/api/v1/meetings",
        json={
            "title": "Passkeys Security Alignment",
            "type": "architecture",
            "scheduled_at": meet_time,
            "duration_minutes": 45,
            "attendee_ids": ["usr_carol"],
        },
        headers=auth(bob_token),
    )
    assert create_resp.status_code == 201
    meeting = create_resp.json()
    assert meeting["status"] == "pending"
    assert meeting["attendee_status"]["usr_carol"] == "pending"
    assert meeting["organiser_name"] == "Bob Harris"
    assert "usr_carol" in meeting["attendee_names"]

    # Check that Carol received a meeting invitation notification
    notif_resp = await client.get("/api/v1/notifications", headers=auth(carol_token))
    assert notif_resp.status_code == 200
    notifications = notif_resp.json()
    invite_notifs = [n for n in notifications if n["type"] == "meeting_invitation" and n["metadata"].get("meeting_id") == meeting["id"]]
    assert len(invite_notifs) >= 1
    assert "Passkeys Security Alignment" in invite_notifs[0]["title"]


@pytest.mark.asyncio
async def test_meeting_rsvp_accept(client: AsyncClient, bob_token: str, carol_token: str):
    # Create meeting
    create_resp = await client.post(
        "/api/v1/meetings",
        json={
            "title": "Zero Trust Gate Review",
            "type": "general",
            "scheduled_at": "2026-11-02T14:00:00",
            "duration_minutes": 30,
            "attendee_ids": ["usr_carol"],
        },
        headers=auth(bob_token),
    )
    assert create_resp.status_code == 201
    meet_id = create_resp.json()["id"]

    # Carol accepts
    rsvp_resp = await client.post(
        f"/api/v1/meetings/{meet_id}/rsvp",
        json={"action": "accept"},
        headers=auth(carol_token),
    )
    assert rsvp_resp.status_code == 200
    res_data = rsvp_resp.json()
    assert res_data["success"] is True
    assert res_data["action"] == "accept"
    assert res_data["meeting"]["status"] == "confirmed"
    assert res_data["meeting"]["attendee_status"]["usr_carol"] == "accepted"

    # Bob should receive acceptance notification
    bob_notifs = await client.get("/api/v1/notifications", headers=auth(bob_token))
    accept_notifs = [n for n in bob_notifs.json() if n["type"] == "meeting_accepted" and n["metadata"].get("meeting_id") == meet_id]
    assert len(accept_notifs) >= 1


@pytest.mark.asyncio
async def test_meeting_rsvp_reject_with_auto_reschedule(client: AsyncClient, bob_token: str, carol_token: str):
    original_time = "2026-11-03T11:00:00"
    proposed_time = "2026-11-03T16:30:00"

    # Bob schedules meeting
    create_resp = await client.post(
        "/api/v1/meetings",
        json={
            "title": "Database Sharding Sync",
            "type": "general",
            "scheduled_at": original_time,
            "duration_minutes": 60,
            "attendee_ids": ["usr_carol"],
        },
        headers=auth(bob_token),
    )
    assert create_resp.status_code == 201
    meet_id = create_resp.json()["id"]

    # Carol rejects and provides reason & available time
    rejection_reason = "Client demo conflict at 11:00 AM; available in late afternoon"
    rsvp_resp = await client.post(
        f"/api/v1/meetings/{meet_id}/rsvp",
        json={
            "action": "reject",
            "rejection_reason": rejection_reason,
            "proposed_time": proposed_time,
        },
        headers=auth(carol_token),
    )
    assert rsvp_resp.status_code == 200
    res = rsvp_resp.json()
    assert res["success"] is True
    assert res["auto_rescheduled"] is True
    updated_meet = res["meeting"]

    # Verify meeting was automatically set to proposed time!
    assert "2026-11-03T16:30:00" in updated_meet["scheduled_at"]
    assert updated_meet["status"] == "rescheduled"
    assert updated_meet["rejection_reason"] == rejection_reason
    assert updated_meet["rescheduled_by"] == "usr_carol"
    assert len(updated_meet["reschedule_history"]) >= 1
    assert updated_meet["reschedule_history"][0]["reason"] == rejection_reason

    # Bob (organiser) must receive reschedule notification
    bob_notifs = await client.get("/api/v1/notifications", headers=auth(bob_token))
    resched_notifs = [n for n in bob_notifs.json() if n["type"] == "meeting_rescheduled" and n["metadata"].get("meeting_id") == meet_id]
    assert len(resched_notifs) >= 1
    assert "automatically rescheduled" in resched_notifs[0]["body"]


@pytest.mark.asyncio
async def test_calendar_collision_detection_and_prevention(client: AsyncClient, bob_token: str, carol_token: str):
    # Bob has an existing call at 2026-11-05 10:00 - 11:00
    base_time = "2026-11-05T10:00:00"
    create1 = await client.post(
        "/api/v1/meetings",
        json={
            "title": "Sprint 45 Kickoff",
            "type": "sprint_planning",
            "scheduled_at": base_time,
            "duration_minutes": 60,
            "attendee_ids": ["usr_carol"],
        },
        headers=auth(bob_token),
    )
    assert create1.status_code == 201

    # Check availability endpoint
    avail_resp = await client.post(
        "/api/v1/meetings/check-availability",
        json={
            "scheduled_at": "2026-11-05T10:30:00",
            "duration_minutes": 30,
            "attendee_ids": ["usr_carol"],
        },
        headers=auth(bob_token),
    )
    assert avail_resp.status_code == 200
    avail_data = avail_resp.json()
    assert avail_data["available"] is False
    assert len(avail_data["conflicts"]) >= 1
    assert avail_data["conflicts"][0]["title"] == "Sprint 45 Kickoff"
    assert len(avail_data["suggested_slots"]) >= 1

    # Attempting to schedule an overlapping call should be rejected with 409 Conflict
    create_collide = await client.post(
        "/api/v1/meetings",
        json={
            "title": "Colliding Call",
            "type": "general",
            "scheduled_at": "2026-11-05T10:30:00",
            "duration_minutes": 30,
            "attendee_ids": ["usr_carol"],
        },
        headers=auth(bob_token),
    )
    assert create_collide.status_code == 409
    err_detail = create_collide.json()["detail"]
    assert "Calendar Collision Alert" in err_detail["message"]
    assert len(err_detail["conflicts"]) >= 1
    assert len(err_detail["suggested_slots"]) >= 1

    # Clear slot check (e.g. 14:00)
    avail_clear = await client.post(
        "/api/v1/meetings/check-availability",
        json={
            "scheduled_at": "2026-11-05T14:00:00",
            "duration_minutes": 30,
            "attendee_ids": ["usr_carol"],
        },
        headers=auth(bob_token),
    )
    assert avail_clear.status_code == 200
    assert avail_clear.json()["available"] is True
