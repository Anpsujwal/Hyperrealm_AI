"""
Tests for Phase 03 — Employee Dashboard, Organization Chart, Role-based Learning, and Admin Console.
"""
import pytest
from .conftest import auth


@pytest.mark.asyncio
async def test_org_tree_includes_priya_and_ayesha(client, carol_token):
    """Org tree should contain Priya Sharma as QA Lead and Ayesha Hussain reporting to Priya."""
    resp = await client.get("/api/v1/users/org/tree", headers=auth(carol_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # Root Alice

    # Flatten helper to search tree
    all_nodes = []
    def flatten(nodes):
        for n in nodes:
            all_nodes.append(n)
            flatten(n.get("reports", []))
    flatten(data)

    user_emails = [n["user"]["email"] for n in all_nodes]
    assert "priya.sharma@hyperrealm.io" in user_emails
    assert "ayesha.hussain@hyperrealm.io" in user_emails

    # Find Priya and verify Ayesha is in her reports
    priya_node = next(n for n in all_nodes if n["user"]["email"] == "priya.sharma@hyperrealm.io")
    report_emails = [r["user"]["email"] for r in priya_node.get("reports", [])]
    assert "ayesha.hussain@hyperrealm.io" in report_emails


@pytest.mark.asyncio
async def test_sensitive_employee_details_access_control(client, alice_token, carol_token, bob_token):
    """
    Sensitive employee details must enforce permissions:
    - Admin (Alice) can view anyone's sensitive details.
    - User (Carol) can view her own sensitive details.
    - Manager (Bob) can view direct report (Carol)'s sensitive details.
    - Non-manager peer (Carol) cannot view Bob's or Alice's sensitive details (403 Forbidden).
    """
    # Carol views her own sensitive details -> 200
    resp_self = await client.get("/api/v1/users/usr_carol/sensitive", headers=auth(carol_token))
    assert resp_self.status_code == 200
    self_data = resp_self.json()
    assert "employee_code" in self_data
    assert "clearance_level" in self_data
    assert "salary_band" in self_data

    # Admin (Alice) views Carol's sensitive details -> 200
    resp_admin = await client.get("/api/v1/users/usr_carol/sensitive", headers=auth(alice_token))
    assert resp_admin.status_code == 200

    # Line manager (Bob) views Carol's sensitive details -> 200
    resp_mgr = await client.get("/api/v1/users/usr_carol/sensitive", headers=auth(bob_token))
    assert resp_mgr.status_code == 200

    # Unauthorized peer: Carol attempts to view Bob's sensitive details -> 403 Forbidden
    resp_unauth = await client.get("/api/v1/users/usr_bob/sensitive", headers=auth(carol_token))
    assert resp_unauth.status_code == 403
    assert "restricted" in resp_unauth.json()["detail"].lower()


@pytest.mark.asyncio
async def test_role_specific_learning_paths(client, carol_token):
    """Test /api/v1/learning/paths returns role-specific items, mandatory flags, and prerequisites."""
    # Request QA Engineer path
    resp_qa = await client.get("/api/v1/learning/paths?role=qa_engineer", headers=auth(carol_token))
    assert resp_qa.status_code == 200
    data_qa = resp_qa.json()
    assert data_qa["role"] == "qa_engineer"
    assert data_qa["total"] >= 15
    titles = [item["title"] for item in data_qa["items"]]
    assert "Testing Standards & Quality Frameworks" in titles
    assert "Python Test Automation with Pytest" in titles
    assert "API Testing & Contract Verification" in titles
    assert "Defect Management & Root Cause Analysis" in titles

    # Check prerequisite tracking
    pytest_mod = next(i for i in data_qa["items"] if i["id"] == "learn_qa_python_automation")
    assert "learn_qa_testing_standards" in pytest_mod["prerequisites"]

    # Request Software Developer path
    resp_dev = await client.get("/api/v1/learning/paths?role=software_developer", headers=auth(carol_token))
    assert resp_dev.status_code == 200
    dev_titles = [item["title"] for item in resp_dev.json()["items"]]
    assert "Secure Coding & OWASP Top 10" in dev_titles
    assert "Scalable Software Architecture & Clean Design" in dev_titles
    assert "REST & Event-Driven API Design Standards" in dev_titles
    assert "Code Review Standards & Peer Governance" in dev_titles


@pytest.mark.asyncio
async def test_admin_console_endpoints_authorized(client, alice_token):
    """Admin user should be able to manage guidelines, document metadata, learning requirements, and ingestion errors."""
    # 1. Guideline changes list
    resp_changes = await client.get("/api/v1/admin/guidelines/changes", headers=auth(alice_token))
    assert resp_changes.status_code == 200
    assert "items" in resp_changes.json()

    # 2. Update guideline metadata
    resp_patch_guide = await client.patch(
        "/api/v1/admin/guidelines/guide_code_review",
        json={"version": "2.2", "status": "published", "changelog": "v2.2: Automated branch protection."},
        headers=auth(alice_token),
    )
    assert resp_patch_guide.status_code == 200
    assert resp_patch_guide.json()["version"] == "2.2"

    # 3. Update document metadata
    resp_patch_doc = await client.patch(
        "/api/v1/admin/documents/doc_security_guide",
        json={"category": "compliance", "is_public": True},
        headers=auth(alice_token),
    )
    assert resp_patch_doc.status_code == 200
    assert resp_patch_doc.json()["category"] == "compliance"

    # 4. Assign learning requirements by role
    resp_assign = await client.put(
        "/api/v1/admin/learning/learn_qa_python_automation/requirements",
        json={"due_days": 21, "required_for_roles": ["qa_engineer", "software_developer"]},
        headers=auth(alice_token),
    )
    assert resp_assign.status_code == 200
    assert resp_assign.json()["due_days"] == 21

    # 5. Ingestion errors list
    resp_errors = await client.get("/api/v1/admin/ingestion-errors", headers=auth(alice_token))
    assert resp_errors.status_code == 200
    assert "items" in resp_errors.json()


@pytest.mark.asyncio
async def test_admin_console_unauthorized_access(client, carol_token):
    """Non-admin user (Software Developer) must receive 403 Forbidden on all admin endpoints."""
    # Guideline changes
    r1 = await client.get("/api/v1/admin/guidelines/changes", headers=auth(carol_token))
    assert r1.status_code == 403

    # Patch guideline
    r2 = await client.patch("/api/v1/admin/guidelines/guide_code_review", json={"version": "9.9"}, headers=auth(carol_token))
    assert r2.status_code == 403

    # Patch document
    r3 = await client.patch("/api/v1/admin/documents/doc_security_guide", json={"category": "hacked"}, headers=auth(carol_token))
    assert r3.status_code == 403

    # Ingestion errors
    r4 = await client.get("/api/v1/admin/ingestion-errors", headers=auth(carol_token))
    assert r4.status_code == 403

    # Audit logs
    r5 = await client.get("/api/v1/admin/audit", headers=auth(carol_token))
    assert r5.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_data_loading(client, carol_token):
    """Test loading of tasks, approvals, meetings, guidelines, and progress for employee dashboard."""
    # My tasks
    t_resp = await client.get("/api/v1/tasks?mine=true", headers=auth(carol_token))
    assert t_resp.status_code == 200

    # Approvals
    a_resp = await client.get("/api/v1/approvals?mine=true", headers=auth(carol_token))
    assert a_resp.status_code == 200

    # Meetings
    m_resp = await client.get("/api/v1/meetings?mine=true", headers=auth(carol_token))
    assert m_resp.status_code == 200

    # Guidelines
    g_resp = await client.get("/api/v1/guidelines", headers=auth(carol_token))
    assert g_resp.status_code == 200

    # Notifications
    n_resp = await client.get("/api/v1/notifications", headers=auth(carol_token))
    assert n_resp.status_code == 200
