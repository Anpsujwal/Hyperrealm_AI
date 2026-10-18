"""
Phase 04 Test Suite: Governed Knowledge Hub, Multimodal Document Intelligence,
and Four-Agent Orchestration.
"""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient

from backend.app.config import get_settings


@pytest.mark.asyncio
async def test_demo_mode_configuration_without_credentials():
    """Scenario 1: Application starts in demo mode without Google Cloud credentials."""
    settings = get_settings()
    diagnostic = settings.validate_cloud_configuration()
    assert diagnostic["app_mode"] == "demo"
    assert diagnostic["configured_model"] == settings.GEMINI_MODEL
    assert diagnostic["fallback_model"] == settings.GEMINI_FALLBACK_MODEL
    assert "local_storage_dir" in diagnostic


@pytest.mark.asyncio
async def test_admin_can_manage_official_guideline_lifecycle(client: AsyncClient, alice_token: str):
    """Scenario 2: Administrator can upload, version, publish, and archive official guidelines."""
    # 1. Admin creates an official guideline
    create_resp = await client.post(
        "/api/v1/official/documents",
        json={
            "title": "HYPERREALM Data Retention Policy",
            "content": "All customer PII must be encrypted at rest and retained for maximum 90 days.",
            "category": "security",
            "version": "1.0",
            "status": "published",
        },
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert create_resp.status_code == 201, create_resp.text
    guide = create_resp.json()
    guide_id = guide["id"]
    assert guide["status"] == "published"
    assert guide["version"] == "1.0"

    # 2. Admin creates a new version (v1.1)
    version_resp = await client.post(
        f"/api/v1/guidelines/{guide_id}/versions",
        json={
            "version": "1.1",
            "title": "HYPERREALM Data Retention Policy v1.1",
            "content": "Updated: Retention window reduced to 60 days with automated purge jobs.",
            "changelog": "Shortened retention period from 90 to 60 days.",
            "status": "published",
        },
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert version_resp.status_code == 200, version_resp.text
    updated_guide = version_resp.json()
    assert updated_guide["version"] == "1.1"

    # 3. Verify version history preserves previous version (v1.0)
    history_resp = await client.get(
        f"/api/v1/guidelines/{guide_id}/versions",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert history_resp.status_code == 200
    versions = history_resp.json()
    assert len(versions) >= 1
    assert any(v["version"] == "1.0" for v in versions)

    # 4. Admin archives the guideline
    archive_resp = await client.patch(
        f"/api/v1/guidelines/{guide_id}/archive",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_guideline_version_diff_and_impact_badges(client: AsyncClient, alice_token: str):
    """Scenario 2b: Compare versions and identify affected roles and Impact Badges."""
    diff_resp = await client.get(
        "/api/v1/guidelines/guide_security_standards/diff?base_version=2.0&target_version=3.0",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert diff_resp.status_code == 200, diff_resp.text
    data = diff_resp.json()
    assert data["guideline_id"] == "guide_security_standards"
    assert data["base_version"] == "2.0"
    assert data["target_version"] == "3.0"
    assert "Impacts: Payments Platform" in data["impact_badges"]
    assert len(data["impacted_roles"]) > 0
    assert data["stats"]["additions"] > 0
    assert len(data["side_by_side"]) > 0
    assert any(line["old_type"] == "removed" or line["new_type"] == "added" for line in data["side_by_side"])



@pytest.mark.asyncio
async def test_employee_read_only_official_guidelines(
    client: AsyncClient, carol_token: str, alice_token: str
):
    """Scenario 3: Non-admin employee can read published guidelines but cannot modify or upload official ones."""
    # Employee can list official published guidelines
    list_resp = await client.get(
        "/api/v1/official/documents",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) > 0

    # Employee CANNOT upload official document (403 Forbidden)
    forbidden_upload = await client.post(
        "/api/v1/official/documents",
        json={
            "title": "Unauthorized Company Policy",
            "content": "Employees may work from anywhere without approval.",
            "category": "policy",
        },
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert forbidden_upload.status_code == 403

    # Employee CANNOT version an official guideline
    guide_id = items[0]["id"]
    forbidden_version = await client.post(
        f"/api/v1/guidelines/{guide_id}/versions",
        json={
            "version": "9.9",
            "title": "Modified Policy",
            "content": "Modified",
            "changelog": "Tampered",
        },
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert forbidden_version.status_code == 403


@pytest.mark.asyncio
async def test_employee_personal_knowledge_hub_upload_and_isolation(
    client: AsyncClient, carol_token: str, eve_token: str
):
    """Scenario 4 & 5: Employee uploads KT doc into personal hub; private from other employees."""
    # Carol uploads a personal KT document
    upload_resp = await client.post(
        "/api/v1/knowledge/personal/documents/upload",
        files={"file": ("payment_flow.txt", b"Payment checkout flow handles tokenization and 3D Secure verification.", "text/plain")},
        data={"title": "Carol Payments Flow KT", "category": "kt", "tags": "payments,checkout"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert upload_resp.status_code == 201, upload_resp.text
    carol_doc = upload_resp.json()
    assert carol_doc["scope"] == "personal"
    doc_id = carol_doc["id"]

    # Carol can view her own personal document
    carol_get = await client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert carol_get.status_code == 200
    assert carol_get.json()["title"] == "Carol Payments Flow KT"

    # Eve (another employee) CANNOT access Carol's private personal document (403 Forbidden)
    eve_get = await client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"Authorization": f"Bearer {eve_token}"},
    )
    assert eve_get.status_code == 403


@pytest.mark.asyncio
async def test_copilot_retrieves_personal_hub_documents(
    client: AsyncClient, carol_token: str
):
    """Scenario 6 & 7: Knowledge Agent retrieves from user's personal hub in later Copilot chat."""
    # User asks question in Copilot chat
    chat_resp = await client.post(
        "/api/v1/chat",
        json={
            "prompt": "How does the payment checkout flow handle tokenization according to my KT documents?",
            "agent_id": "auto",
        },
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert chat_resp.status_code == 200, chat_resp.text
    data = chat_resp.json()
    assert data["agent_id"] == "knowledge"
    assert "tokenization" in data["response"].lower() or "checkout" in data["response"].lower()
    assert len(data["citations"]) > 0
    # Citations reference Carol's document
    assert any("payment" in c.get("title", "").lower() for c in data["citations"])


@pytest.mark.asyncio
async def test_document_summary_and_specific_query(client: AsyncClient, carol_token: str):
    """Scenario 7: Document summary and document-specific query endpoints."""
    # List Carol's documents
    my_docs = await client.get(
        "/api/v1/knowledge/personal/documents",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert my_docs.status_code == 200
    items = my_docs.json()["items"]
    assert len(items) > 0
    target_id = items[0]["id"]

    # Summarize document
    summary_resp = await client.post(
        f"/api/v1/knowledge/documents/{target_id}/summary",
        json={},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert summary_resp.status_code == 200, summary_resp.text
    sum_data = summary_resp.json()
    assert "summary" in sum_data
    assert len(sum_data["key_points"]) > 0

    # Specific grounded query
    query_resp = await client.post(
        f"/api/v1/knowledge/documents/{target_id}/query",
        json={"query": "Explain 3D Secure verification"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert query_resp.status_code == 200, query_resp.text
    assert "citations" in query_resp.json()


@pytest.mark.asyncio
async def test_users_and_admin_can_delete_personal_documents(
    client: AsyncClient, carol_token: str, eve_token: str, alice_token: str
):
    """Scenario 7b: Users and admins can delete personal files; non-authors/non-admins forbidden."""
    # 1. Carol uploads a personal document
    up_resp = await client.post(
        "/api/v1/knowledge/personal/documents/upload",
        files={"file": ("to_delete.txt", b"Temporary testing notes for deletion workflow.", "text/plain")},
        data={"title": "Notes To Delete", "category": "kt"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert up_resp.status_code == 201
    doc_id = up_resp.json()["id"]

    # 2. Eve (non-author, non-admin) cannot delete Carol's document
    forbidden_del = await client.delete(
        f"/api/v1/personal/documents/{doc_id}",
        headers={"Authorization": f"Bearer {eve_token}"},
    )
    assert forbidden_del.status_code == 403

    # 3. Carol (author) can delete her own document
    carol_del = await client.delete(
        f"/api/v1/personal/documents/{doc_id}",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert carol_del.status_code == 204

    # Document no longer exists
    get_del = await client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert get_del.status_code == 404

    # 4. Carol uploads another document, which Admin (Alice) can delete
    up2_resp = await client.post(
        "/api/v1/knowledge/personal/documents/upload",
        files={"file": ("admin_delete.txt", b"Policy cleanup document.", "text/plain")},
        data={"title": "Admin Deletes Me", "category": "kt"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert up2_resp.status_code == 201
    doc2_id = up2_resp.json()["id"]

    admin_del = await client.delete(
        f"/api/v1/knowledge/documents/{doc2_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert admin_del.status_code == 204

    get_del2 = await client.get(
        f"/api/v1/knowledge/documents/{doc2_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert get_del2.status_code == 404


@pytest.mark.asyncio
async def test_brand_compliance_image_audit(client: AsyncClient, alice_token: str):
    """Scenario 8, 10, 11: Brand compliance report cites guideline version and checks."""
    # Test valid image audit
    audit_resp = await client.post(
        "/api/v1/knowledge/images/audit",
        json={
            "image_filename": "hyperrealm_banner.png",
            "image_url": "https://cdn.hyperrealm.io/assets/banner.png",
        },
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert audit_resp.status_code == 200, audit_resp.text
    res = audit_resp.json()
    assert res["status"] in ("compliant", "partially_compliant", "non_compliant")
    assert res["guideline_version"] == "2.1"
    assert len(res["checks"]) > 0
    assert "recommendations" in res
    assert res["analysis_status"] == "simulated_demo"

    # Test non-compliant image audit
    non_comp_resp = await client.post(
        "/api/v1/knowledge/images/audit",
        json={"image_filename": "bad_violating_slide.png"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert non_comp_resp.status_code == 200
    assert non_comp_resp.json()["status"] == "non_compliant"

    # Test empty / ambiguous image audit returns Unable to Determine
    empty_resp = await client.post(
        "/api/v1/knowledge/images/audit",
        json={},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert empty_resp.status_code == 200
    assert empty_resp.json()["status"] == "unable_to_determine"


@pytest.mark.asyncio
async def test_four_specialist_agents_routing(client: AsyncClient, carol_token: str):
    """Scenario 12: HYPERREALM routes correctly to each of the four specialist agents."""
    # 1. Insights Agent: error investigation
    insights_resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "Investigate HTTP 401 error spike in Redis session cache"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert insights_resp.status_code == 200
    assert insights_resp.json()["agent_id"] == "insights"
    assert "incident" in insights_resp.json()["response"].lower()

    # 2. Collaborate Agent: expert finding & meeting scheduling
    collab_resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "Schedule a meeting with an expert on QA testing standards"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert collab_resp.status_code == 200
    assert collab_resp.json()["agent_id"] == "collaborate"
    assert len(collab_resp.json()["proposed_actions"]) > 0

    # 3. Onboard Agent: learning path creation
    onboard_resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "Create an onboarding and learning curriculum for my role"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert onboard_resp.status_code == 200
    assert onboard_resp.json()["agent_id"] == "onboard"
    assert "onboarding" in onboard_resp.json()["response"].lower()

    # 4. Knowledge Agent: personal knowledge query
    knowledge_resp = await client.post(
        "/api/v1/chat",
        json={"prompt": "Summarize my personal KT documentation on payments"},
        headers={"Authorization": f"Bearer {carol_token}"},
    )
    assert knowledge_resp.status_code == 200
    assert knowledge_resp.json()["agent_id"] == "knowledge"


@pytest.mark.asyncio
async def test_action_execution_workflow_and_audit(client: AsyncClient, alice_token: str):
    """Scenario 14: Action execution through workflow with audit logging and idempotency."""
    action_resp = await client.post(
        "/api/v1/actions/execute",
        json={
            "action_type": "schedule_meeting",
            "parameters": {
                "title": "Automated Quality Gate Sync",
                "scheduled_at": "2026-10-20T14:00:00",
                "duration_minutes": 30,
            },
            "idempotency_key": "idemp_test_sync_123",
        },
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert action_resp.status_code == 200, action_resp.text
    record = action_resp.json()
    assert record["status"] == "executed"
    assert record["is_simulated"] is True

    # Idempotent re-execution returns identical record
    repeat_resp = await client.post(
        "/api/v1/actions/execute",
        json={
            "action_type": "schedule_meeting",
            "parameters": {"title": "Automated Quality Gate Sync"},
            "idempotency_key": "idemp_test_sync_123",
        },
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert repeat_resp.status_code == 200
    assert repeat_resp.json()["id"] == record["id"]

    # Verify action execution is recorded in audit log
    audit_resp = await client.get(
        "/api/v1/admin/audit",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert audit_resp.status_code == 200
    audits = audit_resp.json()["items"]
    assert any(a.get("resource_type") == "action_execution" for a in audits)
