"""
Integration tests for dynamic multi-agent collaboration, manager resolution,
and the proposal/confirmation meeting workflow.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from backend.app.dependencies import get_user_repo
from backend.app.models import UserProfile, UserRole


@pytest.mark.asyncio
async def test_single_agent_requests_only_invoke_target_agent(client: AsyncClient, carol_token: str):
    """Verify that single-intent requests only invoke the single necessary specialist agent."""
    headers = {"Authorization": f"Bearer {carol_token}"}

    # 1. Pure knowledge inquiry
    resp_k = await client.post(
        "/api/v1/chat",
        json={"prompt": "What is our company guidelines for code reviews?"},
        headers=headers,
    )
    assert resp_k.status_code == 200
    data_k = resp_k.json()
    assert data_k["agent_id"] == "knowledge"
    assert data_k.get("delegated_agents") == ["knowledge"]

    # 2. Pure onboarding inquiry
    resp_o = await client.post(
        "/api/v1/chat",
        json={"prompt": "What onboarding courses and compliance forms do I need to complete this week?"},
        headers=headers,
    )
    assert resp_o.status_code == 200
    data_o = resp_o.json()
    assert data_o["agent_id"] == "onboard"
    assert data_o.get("delegated_agents") == ["onboard"]

    # 3. Pure insights inquiry
    resp_i = await client.post(
        "/api/v1/chat",
        json={"prompt": "Evaluate the architectural risks and error incident in authentication service"},
        headers=headers,
    )
    assert resp_i.status_code == 200
    data_i = resp_i.json()
    assert data_i["agent_id"] == "insights"
    assert data_i.get("delegated_agents") == ["insights"]


@pytest.mark.asyncio
async def test_multi_agent_onboard_and_collaborate(client: AsyncClient, carol_token: str):
    """
    Scenario: User asks about their onboarding checklist AND asks to schedule a sync with their manager.
    Should dynamically route Onboard first, then Collaborate.
    """
    headers = {"Authorization": f"Bearer {carol_token}"}
    resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "I am onboarding this week, what are my goals and please schedule a meeting with my manager"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()

    # Both agents must have contributed
    assert data["delegated_agents"] == ["onboard", "collaborate"]

    # Final synthesized markdown should show both contributions
    assert "Onboarding & Learning Specialist" in data["response"]
    assert "Collaboration & Team Specialist" in data["response"]

    # Proposed meeting should be included
    assert len(data["proposed_actions"]) > 0
    prop_action = next(a for a in data["proposed_actions"] if a["action_type"] == "schedule_meeting_proposal")
    assert prop_action["payload"]["target_role"] == "Manager"
    # Carol's manager is Bob Harris
    assert prop_action["payload"]["target_name"] == "Bob Harris"
    assert prop_action["payload"]["status"] == "pending_confirmation"


@pytest.mark.asyncio
async def test_multi_agent_incident_knowledge_and_expert_meet(client: AsyncClient, carol_token: str):
    """
    Scenario: A technical incident occurs, user asks to investigate error, check guidelines,
    and schedule a sync with the expert.
    Should route: Insights -> Knowledge -> Collaborate.
    """
    headers = {"Authorization": f"Bearer {carol_token}"}
    resp = await client.post(
        "/api/v1/chat",
        json={
            "prompt": "Investigate 504 Gateway Timeout incident error, verify architectural guidelines, and schedule a meeting with the expert"
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["delegated_agents"] == ["insights", "knowledge", "collaborate"]
    assert "Insights & Architecture Specialist" in data["response"]
    assert "Knowledge Specialist" in data["response"]
    assert "Collaboration & Team Specialist" in data["response"]
    assert len(data["proposed_actions"]) > 0


@pytest.mark.asyncio
async def test_manager_identification_not_ayesha(client: AsyncClient, eve_token: str):
    """
    Verify that when Eve asks to meet with her manager, Priya Sharma is resolved
    from Eve's profile reporting line, and Ayesha Hussain is NOT assumed to be the manager.
    """
    headers = {"Authorization": f"Bearer {eve_token}"}
    resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "Schedule a 1:1 meeting with my manager to discuss my progress"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["proposed_actions"]) > 0
    prop_action = next(a for a in data["proposed_actions"] if a["action_type"] == "schedule_meeting_proposal")

    # Eve Russo reports to Priya Sharma
    assert prop_action["payload"]["target_name"] == "Priya Sharma"
    assert prop_action["payload"]["target_email"] == "priya.sharma@hyperrealm.io"
    assert prop_action["payload"]["target_role"] == "Manager"
    assert "Ayesha" not in prop_action["payload"]["target_name"]


@pytest.mark.asyncio
async def test_unresolved_manager_prompts_user_clarification(client: AsyncClient, alice_token: str):
    """
    Verify that when a user without an assigned manager (like Alice, the CTO) asks for a meeting
    with their manager, the system does not fabricate or guess, but asks the user for clarification.
    """
    headers = {"Authorization": f"Bearer {alice_token}"}
    resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "Please schedule a meeting with my manager"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()

    # Should ask clarification
    assert "could not identify your direct reporting manager" in data["response"].lower()
    # No proposal or scheduled meeting should be created
    assert len(data["proposed_actions"]) == 0


@pytest.mark.asyncio
async def test_meeting_proposal_lifecycle_confirm_and_reschedule(client: AsyncClient, carol_token: str):
    """
    Test the full proposal lifecycle:
    1. Create/propose meeting (remains in pending_confirmation, not yet on calendar).
    2. 'Choose Another Time' updates proposal without scheduling.
    3. 'Confirm & Schedule' executes and marks as confirmed.
    4. Duplicate confirm protection prevents double booking.
    """
    headers = {"Authorization": f"Bearer {carol_token}"}

    # 1. Propose meeting via Collaborate Agent
    chat_resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "Schedule a meeting with Bob Harris about code review guidelines"},
        headers=headers,
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert len(chat_data["proposed_actions"]) > 0

    prop_action = next(a for a in chat_data["proposed_actions"] if a["action_type"] == "schedule_meeting_proposal")
    proposal_id = prop_action["payload"]["proposal_id"]
    assert proposal_id is not None

    # Verify proposal is in pending_confirmation state
    prop_resp = await client.get(f"/api/v1/meetings/proposals/{proposal_id}", headers=headers)
    assert prop_resp.status_code == 200
    proposal = prop_resp.json()
    assert proposal["status"] == "pending_confirmation"
    assert proposal["meeting_id"] is None
    assert proposal["target_name"] == "Bob Harris"

    # 2. User selects "Choose Another Time"
    new_time = "2026-10-25T14:30:00"
    update_resp = await client.patch(
        f"/api/v1/meetings/proposals/{proposal_id}",
        json={"scheduled_at": new_time, "duration_minutes": 45},
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated_prop = update_resp.json()
    assert updated_prop["status"] == "pending_confirmation"
    assert updated_prop["duration_minutes"] == 45
    assert "2026-10-25" in updated_prop["scheduled_at"]

    # 3. User clicks "Confirm & Schedule"
    confirm_resp = await client.post(
        f"/api/v1/meetings/proposals/{proposal_id}/confirm",
        headers=headers,
    )
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["success"] is True
    assert confirm_data["proposal"]["status"] == "confirmed"
    assert confirm_data["meeting"]["id"] is not None
    assert confirm_data["meeting"]["duration_minutes"] == 45

    # 4. Duplicate click retry protection
    retry_resp = await client.post(
        f"/api/v1/meetings/proposals/{proposal_id}/confirm",
        headers=headers,
    )
    assert retry_resp.status_code == 200
    retry_data = retry_resp.json()
    assert retry_data.get("already_scheduled") is True
