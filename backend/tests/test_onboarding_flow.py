"""
End-to-end test suite for HYPERREALM Onboarding Flow across all 4 Phases:
1. Personalized onboarding & intelligent learning plan generation
2. Manager approval workflow and automatic My Learning course assignment
3. Automated introductions, meetings, forms, documents, and privacy protection
4. Agent orchestration, question answering, and RBAC enforcement
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from backend.app.models import ApprovalStatus, LearningStatus, OnboardingFormStatus, UserRole


@pytest.mark.asyncio
async def test_personalized_onboarding_plan_generation(
    client: AsyncClient,
    carol_token: str,
):
    """Phase 1: Verify associate receives a personalized onboarding plan with all requirements."""
    resp = await client.get(
        "/api/v1/onboarding/journey",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["role"] == "software_developer"
    assert data["department"] == "Engineering"
    assert data["manager_name"] == "Bob Harris"
    assert data["buddy_name"] is not None

    # Verify courses
    courses = data["courses"]
    assert len(courses) > 0
    mandatory_courses = [c for c in courses if c["is_mandatory"]]
    elective_courses = [c for c in courses if not c["is_mandatory"]]
    assert len(mandatory_courses) > 0
    assert len(elective_courses) > 0
    for c in courses:
        assert "resource_id" in c
        assert "title" in c
        assert "reason" in c
        assert "estimated_minutes" in c

    # Verify introductions
    intros = data["introductions"]
    assert len(intros) >= 2
    relationships = [i["relationship"] for i in intros]
    assert "Reporting Manager" in relationships

    # Verify required forms
    forms = data["forms"]
    assert len(forms) == 5
    form_ids = [f["id"] for f in forms]
    assert "form_i9_identity" in form_ids
    assert "form_direct_deposit" in form_ids
    assert "form_code_of_conduct" in form_ids
    assert "form_nda_ip" in form_ids
    assert "form_security_compliance" in form_ids

    # Verify normalized steps contract: BOTH onboarding_steps and onboardingSteps must be lists
    assert isinstance(data["onboarding_steps"], list)
    assert isinstance(data["onboardingSteps"], list)
    assert len(data["onboarding_steps"]) >= 3
    # Check that .filter on steps works without error
    filtered = [s for s in data["onboarding_steps"] if s.get("phase") == "Day 1"]
    assert len(filtered) == 1


@pytest.mark.asyncio
async def test_manager_course_approval_request_flow(
    client: AsyncClient,
    carol_token: str,
    bob_token: str,
):
    """Phase 2: Associate requests manager approval for proposed courses."""
    # 1. Carol requests approval for 2 courses
    course_ids = ["learn_dev_architecture", "learn_dev_api_design"]
    req_resp = await client.post(
        "/api/v1/onboarding/request-approval",
        json={
            "course_ids": course_ids,
            "justification": "Required for Project Phoenix backend API redesign and microservices.",
        },
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert req_resp.status_code == 200
    req_data = req_resp.json()
    assert "approval" in req_data
    approval_id = req_data["approval"]["id"]
    assert req_data["approval"]["status"] == "pending"
    assert req_data["approval"]["action_type"] == "course_assignment_approval"

    # 2. Bob (manager) lists approval requests and sees Carol's request
    mgr_resp = await client.get(
        "/api/v1/onboarding/manager/requests",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert mgr_resp.status_code == 200
    requests = mgr_resp.json()
    matching = [r for r in requests if r["id"] == approval_id]
    assert len(matching) == 1
    assert matching[0]["requester_id"] == "usr_carol"
    assert matching[0]["is_pending"] is True


@pytest.mark.asyncio
async def test_manager_approval_modification_and_automatic_assignment(
    client: AsyncClient,
    carol_token: str,
    bob_token: str,
):
    """Phase 2: Manager modifies and approves courses, verifying automatic assignment into My Learning."""
    # 1. Carol requests 2 courses
    course_ids = ["learn_dev_architecture", "learn_dev_api_design"]
    req_resp = await client.post(
        "/api/v1/onboarding/request-approval",
        json={"course_ids": course_ids, "justification": "Architecture track."},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    approval_id = req_resp.json()["approval"]["id"]

    # 2. Bob approves, modifying to select only 1 course
    approved_selection = ["learn_dev_architecture"]
    resolve_resp = await client.post(
        f"/api/v1/onboarding/approvals/{approval_id}/resolve",
        json={
            "status": "approved",
            "decision_note": "Approved core architecture module; defer API design to Sprint 43.",
            "approved_course_ids": approved_selection,
        },
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert resolve_resp.status_code == 200
    res_data = resolve_resp.json()
    assert res_data["status"] == "approved"

    # 3. Verify automatic assignment in Carol's My Learning
    learning_resp = await client.get(
        "/api/v1/learning/paths?only_role_and_mandatory=true",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert learning_resp.status_code == 200
    learning_data = learning_resp.json()
    items = learning_data["items"]
    approved_item = next((i for i in items if i["id"] == "learn_dev_architecture"), None)
    assert approved_item is not None
    assert approved_item["status"] in ("not_started", "in_progress", "completed")


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_resolve_approval(
    client: AsyncClient,
    carol_token: str,
    eve_token: str,
):
    """Phase 2: Unauthorized peer cannot approve courses."""
    # Carol requests approval
    req_resp = await client.post(
        "/api/v1/onboarding/request-approval",
        json={"course_ids": ["learn_dev_architecture"], "justification": "Peer test."},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    approval_id = req_resp.json()["approval"]["id"]

    # David (peer, not manager) attempts to resolve
    fail_resp = await client.post(
        f"/api/v1/onboarding/approvals/{approval_id}/resolve",
        json={"status": "approved", "decision_note": "Peer bypass attempt"},
        headers={"Authorization": f"Bearer {eve_token}"},
    )
    assert fail_resp.status_code == 403


@pytest.mark.asyncio
async def test_introductions_and_meeting_scheduling(
    client: AsyncClient,
    carol_token: str,
):
    """Phase 3: Associate schedules an onboarding introduction meeting."""
    # Get journey to find an intro ID
    j_resp = await client.get(
        "/api/v1/onboarding/journey",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    journey = j_resp.json()
    intro = journey["introductions"][0]
    intro_id = intro["id"]

    # Schedule the meeting
    sched_resp = await client.post(
        "/api/v1/onboarding/schedule-intro",
        json={
            "intro_id": intro_id,
            "duration_minutes": 30,
            "notes": "Discuss Sprint 42 onboarding and repo access.",
        },
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json()
    assert "meeting_id" in sched_data
    meeting_id = sched_data["meeting_id"]

    # Verify meeting exists in meeting service
    meeting_check = await client.get(
        f"/api/v1/meetings/{meeting_id}",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert meeting_check.status_code == 200
    m_data = meeting_check.json()
    assert "usr_carol" in m_data["attendee_ids"]


@pytest.mark.asyncio
async def test_forms_submission_validation_and_sensitive_protection(
    client: AsyncClient,
    carol_token: str,
    eve_token: str,
):
    """Phase 3: Form submission validation and RBAC protection of sensitive details."""
    # 1. Validation error when required field is missing
    bad_resp = await client.post(
        "/api/v1/onboarding/forms/form_i9_identity/submit",
        json={"form_data": {"document_type": "Passport"}},  # missing document_number
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert bad_resp.status_code == 400

    # 2. Valid submission
    good_resp = await client.post(
        "/api/v1/onboarding/forms/form_i9_identity/submit",
        json={
            "form_data": {
                "document_type": "US Passport",
                "document_number": "A12345678",
                "issuing_authority": "US Department of State",
            },
            "signature_confirmation": True,
        },
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert good_resp.status_code == 200
    good_data = good_resp.json()
    assert good_data["status"] == "submitted"

    # 3. Sensitive protection: David (unauthorized peer) cannot view Carol's journey
    peer_view = await client.get(
        "/api/v1/onboarding/user/usr_carol",
        headers={"Authorization": f"Bearer {eve_token}"},
    )
    assert peer_view.status_code == 403


@pytest.mark.asyncio
async def test_onboard_agent_orchestration_and_qa(
    client: AsyncClient,
    carol_token: str,
):
    """Phase 4: Associate asks Onboard Agent domain questions and receives live context-aware answers."""
    # Question 1: What do I need to complete this week?
    resp_week = await client.post(
        "/api/v1/chat",
        json={"prompt": "What do I need to complete this week?", "agent_id": "onboard"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert resp_week.status_code == 200
    data_week = resp_week.json()
    assert data_week["agent_id"] == "onboard"
    content_week = data_week["response"].lower()
    assert "week" in content_week or "priority" in content_week

    # Question 2: Which courses are waiting for manager approval?
    resp_appr = await client.post(
        "/api/v1/chat",
        json={"prompt": "Which courses are waiting for manager approval?", "agent_id": "onboard"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert resp_appr.status_code == 200
    data_appr = resp_appr.json()
    content_appr = data_appr["response"].lower()
    assert "approval" in content_appr or "courses" in content_appr

    # Question 3: Who should I meet next?
    resp_meet = await client.post(
        "/api/v1/chat",
        json={"prompt": "Who should I meet next?", "agent_id": "onboard"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert resp_meet.status_code == 200
    data_meet = resp_meet.json()
    content_meet = data_meet["response"].lower()
    assert "meet" in content_meet or "introduction" in content_meet or "bob harris" in content_meet

    # Question 4: Which forms are pending?
    resp_forms = await client.post(
        "/api/v1/chat",
        json={"prompt": "Which forms are pending?", "agent_id": "onboard"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert resp_forms.status_code == 200
    data_forms = resp_forms.json()
    content_forms = data_forms["response"].lower()
    assert "form" in content_forms or "pending" in content_forms
