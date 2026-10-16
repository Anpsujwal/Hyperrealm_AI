"""
Phase 03 seed script.
Seeds Priya Sharma, Ayesha Hussain, full role-specific learning paths,
guideline versions, KT sessions, pending approvals, deadlines/overdue tasks,
and audit/ingestion errors into hyperrealm.db.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from .auth import hash_password
from .config import get_settings
from .dependencies import init_repositories, get_user_repo, get_project_repo, get_guide_repo, get_learning_repo, get_meeting_repo, get_task_repo, get_approval_repo, get_notif_repo, get_audit_repo, get_doc_repo
from .models import (
    Approval,
    ApprovalStatus,
    AuditAction,
    AuditRecord,
    Document,
    Guideline,
    LearningResource,
    LearningStatus,
    Meeting,
    MeetingType,
    Notification,
    NotificationType,
    Project,
    ProjectStatus,
    Task,
    TaskPriority,
    TaskStatus,
    UserLearningProgress,
    UserProfile,
    UserRole,
    UserStatus,
    utcnow,
)

_NOW = datetime.utcnow()

def _dt(days: int = 0, hours: int = 0) -> datetime:
    return _NOW + timedelta(days=days, hours=hours)


async def run_phase3_seed():
    init_repositories()

    user_repo = get_user_repo()
    project_repo = get_project_repo()
    guide_repo = get_guide_repo()
    learning_repo = get_learning_repo()
    meeting_repo = get_meeting_repo()
    task_repo = get_task_repo()
    approval_repo = get_approval_repo()
    notif_repo = get_notif_repo()
    audit_repo = get_audit_repo()
    doc_repo = get_doc_repo()

    pw = hash_password("Password123!")

    # ── 1. Users ─────────────────────────────────────────────────────────────
    # Check or create Priya Sharma (QA Lead, reports to Bob Harris)
    priya = await user_repo.get_by_email("priya.sharma@hyperrealm.io")
    if not priya:
        priya = UserProfile(
            id="usr_priya",
            email="priya.sharma@hyperrealm.io",
            name="Priya Sharma",
            role=UserRole.TECHNICAL_LEAD,
            department_id="dept_engineering",
            department_name="Engineering",
            job_title="QA Lead",
            manager_id="usr_bob",
            hashed_password=pw,
            skills=["Test Architecture", "Python Automation", "Selenium", "API Testing", "CI/CD Quality Gates"],
            project_ids=["proj_phoenix", "proj_sentinel"],
            status=UserStatus.ACTIVE,
            created_at=_dt(-140),
        )
        await user_repo.create(priya)
        print("Created Priya Sharma")
    else:
        priya.job_title = "QA Lead"
        priya.manager_id = "usr_bob"
        priya.project_ids = ["proj_phoenix", "proj_sentinel"]
        await user_repo.update(priya)

    # Check or create Ayesha Hussain (QA Engineer, reports to Priya Sharma)
    ayesha = await user_repo.get_by_email("ayesha.hussain@hyperrealm.io")
    if not ayesha:
        ayesha = UserProfile(
            id="usr_ayesha",
            email="ayesha.hussain@hyperrealm.io",
            name="Ayesha Hussain",
            role=UserRole.QA_ENGINEER,
            department_id="dept_engineering",
            department_name="Engineering",
            job_title="QA Engineer",
            manager_id="usr_priya",
            hashed_password=pw,
            skills=["Python Automation", "Pytest", "API Testing", "Postman", "Defect Management", "Jira"],
            project_ids=["proj_phoenix"],
            status=UserStatus.ACTIVE,
            created_at=_dt(-80),
        )
        await user_repo.create(ayesha)
        print("Created Ayesha Hussain")
    else:
        ayesha.role = UserRole.QA_ENGINEER
        ayesha.job_title = "QA Engineer"
        ayesha.manager_id = "usr_priya"
        ayesha.project_ids = ["proj_phoenix"]
        await user_repo.update(ayesha)

    # Update Eve Russo to report to Priya Sharma
    eve = await user_repo.get_by_email("eve.russo@hyperrealm.io")
    if eve:
        eve.manager_id = "usr_priya"
        await user_repo.update(eve)

    # ── 2. Projects ──────────────────────────────────────────────────────────
    phoenix = await project_repo.get("proj_phoenix")
    if phoenix:
        phoenix.member_ids = list(set(phoenix.member_ids + ["usr_priya", "usr_ayesha", "usr_carol", "usr_eve"]))
        await project_repo.update(phoenix)

    sentinel = await project_repo.get("proj_sentinel")
    if sentinel:
        sentinel.member_ids = list(set(sentinel.member_ids + ["usr_priya", "usr_bob", "usr_frank"]))
        await project_repo.update(sentinel)

    # ── 3. Role-specific Learning Resources (Section C) ─────────────────────
    learning_resources = [
        # QA Engineer
        LearningResource(
            id="learn_qa_testing_standards",
            title="Testing Standards & Quality Frameworks",
            description="Comprehensive guide to unit, integration, end-to-end testing gates and acceptance criteria.",
            category="engineering",
            estimated_minutes=120,
            required_for_roles=[UserRole.QA_ENGINEER],
            tags=["qa", "testing", "standards", "quality"],
            prerequisites=[],
            due_days=14,
        ),
        LearningResource(
            id="learn_qa_python_automation",
            title="Python Test Automation with Pytest",
            description="Developing resilient automated test suites, fixtures, parametrisation, and mocking in Python.",
            category="engineering",
            estimated_minutes=180,
            required_for_roles=[UserRole.QA_ENGINEER],
            tags=["python", "pytest", "automation"],
            prerequisites=["learn_qa_testing_standards"],
            due_days=30,
        ),
        LearningResource(
            id="learn_qa_api_testing",
            title="API Testing & Contract Verification",
            description="RESTful endpoint validation, schema contracts, Postman collections, and regression test suites.",
            category="engineering",
            estimated_minutes=150,
            required_for_roles=[UserRole.QA_ENGINEER],
            tags=["api", "contract-testing", "postman"],
            prerequisites=["learn_qa_testing_standards"],
            due_days=30,
        ),
        LearningResource(
            id="learn_qa_defect_management",
            title="Defect Management & Root Cause Analysis",
            description="Triage workflows, bug lifecycle tracking, RCA blameless reviews, and defect prevention.",
            category="process",
            estimated_minutes=90,
            required_for_roles=[UserRole.QA_ENGINEER],
            tags=["defect", "jira", "rca", "quality"],
            prerequisites=[],
            due_days=21,
        ),

        # Software Developer
        LearningResource(
            id="learn_dev_secure_coding",
            title="Secure Coding & OWASP Top 10",
            description="Mitigating injection vulnerabilities, memory safety, input validation, and secure auth handling.",
            category="security",
            estimated_minutes=120,
            required_for_roles=[UserRole.SOFTWARE_DEVELOPER, UserRole.TECHNICAL_LEAD],
            tags=["security", "owasp", "vulnerability"],
            prerequisites=[],
            due_days=14,
        ),
        LearningResource(
            id="learn_dev_architecture",
            title="Scalable Software Architecture & Clean Design",
            description="Hexagonal architecture, domain-driven design principles, decoupled services, and caching patterns.",
            category="engineering",
            estimated_minutes=200,
            required_for_roles=[UserRole.SOFTWARE_DEVELOPER, UserRole.TECHNICAL_LEAD],
            tags=["architecture", "ddd", "design-patterns"],
            prerequisites=[],
            due_days=30,
        ),
        LearningResource(
            id="learn_dev_api_design",
            title="REST & Event-Driven API Design Standards",
            description="Contract-first OpenAPI schemas, versioning schemes, idempotency, and asynchronous event streams.",
            category="engineering",
            estimated_minutes=160,
            required_for_roles=[UserRole.SOFTWARE_DEVELOPER],
            tags=["api", "openapi", "rest", "backend"],
            prerequisites=[],
            due_days=30,
        ),
        LearningResource(
            id="learn_dev_code_reviews",
            title="Code Review Standards & Peer Governance",
            description="Constructive peer review guidelines, PR size limits, automated linters, and quality gates.",
            category="process",
            estimated_minutes=90,
            required_for_roles=[UserRole.SOFTWARE_DEVELOPER, UserRole.TECHNICAL_LEAD],
            tags=["code-review", "quality", "governance"],
            prerequisites=[],
            due_days=21,
        ),

        # DevOps Engineer
        LearningResource(
            id="learn_ops_cicd",
            title="CI/CD Pipeline Automation & Production Gates",
            description="GitHub Actions workflows, automated build caching, canary rollouts, and artifact signing.",
            category="devops",
            estimated_minutes=180,
            required_for_roles=[UserRole.DEVOPS_ENGINEER],
            tags=["ci-cd", "github-actions", "deployment"],
            prerequisites=[],
            due_days=21,
        ),
        LearningResource(
            id="learn_ops_cloud_sec",
            title="Cloud Security & IAM Governance",
            description="Principle of least privilege in GCP/AWS, Workload Identity Federation, and secrets management.",
            category="security",
            estimated_minutes=150,
            required_for_roles=[UserRole.DEVOPS_ENGINEER],
            tags=["cloud", "security", "iam", "gcp"],
            prerequisites=[],
            due_days=14,
        ),
        LearningResource(
            id="learn_ops_monitoring",
            title="System Observability & SRE Telemetry",
            description="Prometheus metric collection, Grafana dashboards, SLI/SLO threshold alerting, and distributed tracing.",
            category="devops",
            estimated_minutes=160,
            required_for_roles=[UserRole.DEVOPS_ENGINEER],
            tags=["observability", "prometheus", "grafana", "sre"],
            prerequisites=[],
            due_days=30,
        ),
        LearningResource(
            id="learn_ops_incident",
            title="Incident Response Runbooks & SRE Best Practices",
            description="On-call escalation paths, P1 bridge protocols, status page updates, and post-mortem facilitation.",
            category="devops",
            estimated_minutes=120,
            required_for_roles=[UserRole.DEVOPS_ENGINEER, UserRole.TECHNICAL_LEAD],
            tags=["incident", "sre", "runbook"],
            prerequisites=[],
            due_days=21,
        ),

        # Project Manager / Scrum Master
        LearningResource(
            id="learn_pm_scrum",
            title="Scrum Framework & Ceremony Facilitation",
            description="Sprint planning efficiency, daily standup timeboxing, sprint reviews, and actionable retrospectives.",
            category="process",
            estimated_minutes=150,
            required_for_roles=[UserRole.PROJECT_MANAGER],
            tags=["scrum", "agile", "ceremonies"],
            prerequisites=[],
            due_days=14,
        ),
        LearningResource(
            id="learn_pm_delivery",
            title="Delivery Governance & Agile Metrics",
            description="Sprint velocity analysis, burndown chart interpretation, blocker tracking, and stakeholder communication.",
            category="process",
            estimated_minutes=120,
            required_for_roles=[UserRole.PROJECT_MANAGER],
            tags=["governance", "metrics", "velocity"],
            prerequisites=[],
            due_days=30,
        ),
        LearningResource(
            id="learn_pm_risk",
            title="Agile Risk Management & Mitigation",
            description="Identifying technical debt, dependency mapping, buffer allocation, and project roadmapping.",
            category="process",
            estimated_minutes=110,
            required_for_roles=[UserRole.PROJECT_MANAGER],
            tags=["risk", "planning", "roadmap"],
            prerequisites=[],
            due_days=30,
        ),

        # Technical Lead
        LearningResource(
            id="learn_lead_arch_review",
            title="Architecture Review Board (ARB) Standards",
            description="Evaluating architectural proposals, non-functional requirements, scalability, and security posture.",
            category="engineering",
            estimated_minutes=180,
            required_for_roles=[UserRole.TECHNICAL_LEAD],
            tags=["architecture", "arb", "lead"],
            prerequisites=[],
            due_days=21,
        ),
        LearningResource(
            id="learn_lead_threat_model",
            title="STRIDE Threat Modelling for Enterprise Services",
            description="Conducting structured threat assessments, data flow diagrams, and vulnerability mitigations.",
            category="security",
            estimated_minutes=160,
            required_for_roles=[UserRole.TECHNICAL_LEAD],
            tags=["threat-modeling", "stride", "security"],
            prerequisites=[],
            due_days=21,
        ),
        LearningResource(
            id="learn_lead_adr",
            title="Technical Decision Records (ADRs) & Trade-offs",
            description="Documenting critical engineering decisions, context, consequences, and historical trade-offs.",
            category="process",
            estimated_minutes=100,
            required_for_roles=[UserRole.TECHNICAL_LEAD],
            tags=["adr", "documentation", "decisions"],
            prerequisites=[],
            due_days=30,
        ),

        # New Employee (Mandatory for all roles)
        LearningResource(
            id="learn_onboard_policies",
            title="Company Policies, Culture & Workplace Code",
            description="Hyperrealm workplace standards, hybrid working etiquette, conduct code, and employee perks.",
            category="hr",
            estimated_minutes=60,
            required_for_roles=[UserRole.EMPLOYEE, UserRole.QA_ENGINEER, UserRole.SOFTWARE_DEVELOPER, UserRole.DEVOPS_ENGINEER, UserRole.PROJECT_MANAGER, UserRole.TECHNICAL_LEAD, UserRole.ADMIN],
            tags=["onboarding", "policy", "hr"],
            prerequisites=[],
            due_days=7,
        ),
        LearningResource(
            id="learn_onboard_privacy",
            title="Data Protection, Privacy & GDPR Fundamentals",
            description="Handling customer personally identifiable information (PII), retention schedules, and GDPR rights.",
            category="security",
            estimated_minutes=75,
            required_for_roles=[UserRole.EMPLOYEE, UserRole.QA_ENGINEER, UserRole.SOFTWARE_DEVELOPER, UserRole.DEVOPS_ENGINEER, UserRole.PROJECT_MANAGER, UserRole.TECHNICAL_LEAD, UserRole.ADMIN],
            tags=["privacy", "gdpr", "compliance"],
            prerequisites=[],
            due_days=7,
        ),
        LearningResource(
            id="learn_onboard_kt",
            title="HYPERREALM Platform Knowledge Transfer (KT)",
            description="Architecture orientation, core services, microservices ecosystem, and local development environment setup.",
            category="engineering",
            estimated_minutes=120,
            required_for_roles=[UserRole.EMPLOYEE, UserRole.QA_ENGINEER, UserRole.SOFTWARE_DEVELOPER, UserRole.DEVOPS_ENGINEER, UserRole.PROJECT_MANAGER, UserRole.TECHNICAL_LEAD, UserRole.ADMIN],
            tags=["kt", "platform", "architecture"],
            prerequisites=["learn_onboard_policies"],
            due_days=14,
        ),
        LearningResource(
            id="learn_onboard_mandatory",
            title="Mandatory Workstation & Cybersecurity Training",
            description="Device encryption, MFA token hygiene, phishing simulation awareness, and reporting suspicious activity.",
            category="security",
            estimated_minutes=90,
            required_for_roles=[UserRole.EMPLOYEE, UserRole.QA_ENGINEER, UserRole.SOFTWARE_DEVELOPER, UserRole.DEVOPS_ENGINEER, UserRole.PROJECT_MANAGER, UserRole.TECHNICAL_LEAD, UserRole.ADMIN],
            tags=["security", "mandatory", "cyber"],
            prerequisites=[],
            due_days=14,
        ),
    ]

    for r in learning_resources:
        existing = await learning_repo.get_resource(r.id)
        if not existing:
            await learning_repo.create_resource(r)
        else:
            if hasattr(learning_repo, "update_resource"):
                await learning_repo.update_resource(r)
    print("Seeded learning resources")

    # ── 4. Learning Progress for Users ──────────────────────────────────────
    user_progress_seeds = [
        # Ayesha Hussain progress
        UserLearningProgress(
            id="ulp_ayesha_1",
            user_id="usr_ayesha",
            resource_id="learn_onboard_policies",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-30),
            completed_at=_dt(-28),
        ),
        UserLearningProgress(
            id="ulp_ayesha_2",
            user_id="usr_ayesha",
            resource_id="learn_onboard_privacy",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-27),
            completed_at=_dt(-25),
        ),
        UserLearningProgress(
            id="ulp_ayesha_3",
            user_id="usr_ayesha",
            resource_id="learn_qa_testing_standards",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-20),
            completed_at=_dt(-15),
        ),
        UserLearningProgress(
            id="ulp_ayesha_4",
            user_id="usr_ayesha",
            resource_id="learn_qa_python_automation",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=65,
            started_at=_dt(-10),
            due_date=_dt(5),
        ),
        UserLearningProgress(
            id="ulp_ayesha_5",
            user_id="usr_ayesha",
            resource_id="learn_qa_api_testing",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=30,
            started_at=_dt(-4),
            due_date=_dt(12),
        ),

        # Priya Sharma progress
        UserLearningProgress(
            id="ulp_priya_1",
            user_id="usr_priya",
            resource_id="learn_qa_testing_standards",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-90),
            completed_at=_dt(-85),
        ),
        UserLearningProgress(
            id="ulp_priya_2",
            user_id="usr_priya",
            resource_id="learn_lead_arch_review",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-70),
            completed_at=_dt(-60),
        ),
        UserLearningProgress(
            id="ulp_priya_3",
            user_id="usr_priya",
            resource_id="learn_lead_threat_model",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=80,
            started_at=_dt(-14),
            due_date=_dt(7),
        ),

        # Carol Adams progress
        UserLearningProgress(
            id="ulp_carol_dev_secure",
            user_id="usr_carol",
            resource_id="learn_dev_secure_coding",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=75,
            started_at=_dt(-12),
            due_date=_dt(4),
        ),
        UserLearningProgress(
            id="ulp_carol_dev_arch",
            user_id="usr_carol",
            resource_id="learn_dev_architecture",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=40,
            started_at=_dt(-6),
            due_date=_dt(15),
        ),
        UserLearningProgress(
            id="ulp_carol_dev_reviews",
            user_id="usr_carol",
            resource_id="learn_dev_code_reviews",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-40),
            completed_at=_dt(-30),
        ),
        UserLearningProgress(
            id="ulp_carol_onboard_policies",
            user_id="usr_carol",
            resource_id="learn_onboard_policies",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-100),
            completed_at=_dt(-98),
        ),
    ]
    for ulp in user_progress_seeds:
        await learning_repo.upsert_progress(ulp)
    print("Seeded user progress records")

    # ── 5. Guidelines with Versioning & Scope (Section D) ───────────────────
    guidelines_phase3 = [
        Guideline(
            id="guide_code_review",
            title="Code Review Guidelines & PR Governance",
            content="All pull requests require approving peer review and QA sign-off before merge. Maximum 400 lines per PR. Automated CI tests must achieve minimum 85% branch coverage.",
            category="engineering",
            owner_id="usr_bob",
            version="2.1",
            status="published",
            effective_date=_dt(-60),
            review_date=_dt(120),
            tags=["code-review", "engineering", "pr-gates"],
            affected_teams=["Engineering", "QA", "Product"],
            affected_projects=["Project Phoenix", "Project Sentinel"],
            changelog="v2.1: Enforced mandatory QA sign-off for release branches.",
        ),
        Guideline(
            id="guide_incident_response",
            title="Incident Response Runbook & Severity Matrix",
            content="P1 outages require bridge assembly within 15 minutes. Root cause analysis (RCA) must be published to Knowledge Hub within 5 business days.",
            category="security",
            owner_id="usr_frank",
            version="3.0",
            status="published",
            effective_date=_dt(-90),
            review_date=_dt(90),
            tags=["incident", "sre", "on-call", "security"],
            affected_teams=["DevOps", "Engineering", "Operations"],
            affected_projects=["Project Sentinel", "All Services"],
            changelog="v3.0: Added automated PagerDuty escalation and Slack bridge channels.",
        ),
        Guideline(
            id="guide_qa_standards",
            title="QA Test Automation & Acceptance Criteria",
            content="Standardized pytest and cypress test patterns. Automated regression suite must execute on staging prior to each production release.",
            category="engineering",
            owner_id="usr_priya",
            version="1.4",
            status="published",
            effective_date=_dt(-20),
            review_date=_dt(160),
            tags=["qa", "testing", "automation", "quality"],
            affected_teams=["QA", "Engineering"],
            affected_projects=["Project Phoenix"],
            changelog="v1.4: Introduced Playwright E2E guidelines and contract testing SLA.",
        ),
        Guideline(
            id="guide_agile_delivery",
            title="Agile Delivery & Scrum Governance Playbook",
            content="Two-week sprint cadences. Backlog refinement occurs every Wednesday. Definition of Done entails code complete, peer reviewed, and automated tests passing.",
            category="process",
            owner_id="usr_henry",
            version="2.0",
            status="published",
            effective_date=_dt(-45),
            review_date=_dt(135),
            tags=["agile", "scrum", "sprints", "process"],
            affected_teams=["Product", "Engineering", "QA"],
            affected_projects=["Project Phoenix"],
            changelog="v2.0: Standardized story point estimation scale and DoD criteria.",
        ),
        Guideline(
            id="guide_data_protection",
            title="Data Protection, Privacy & GDPR Standard",
            content="Zero raw customer PII in application logs. All database backups must use AES-256 encryption. Retention limits enforced strictly at 90 days for operational logs.",
            category="security",
            owner_id="usr_alice",
            version="1.8",
            status="published",
            effective_date=_dt(-30),
            review_date=_dt(150),
            tags=["gdpr", "privacy", "compliance", "security"],
            affected_teams=["All Teams"],
            affected_projects=["Project Phoenix", "Project Sentinel"],
            changelog="v1.8: Updated data residency rules for EU cloud regions.",
        ),
    ]
    for g in guidelines_phase3:
        existing = await guide_repo.get(g.id)
        if not existing:
            await guide_repo.create(g)
        else:
            await guide_repo.update(g)
    print("Seeded guidelines")

    # ── 6. Upcoming Scrum Meetings & KT Sessions (Section A) ────────────────
    meetings_phase3 = [
        Meeting(
            id="meet_daily_scrum_phoenix",
            title="Daily Scrum — Phoenix Squad",
            type=MeetingType.STANDUP,
            description="15-minute daily sync: yesterday's achievements, today's goals, and active blockers.",
            organiser_id="usr_henry",
            attendee_ids=["usr_bob", "usr_carol", "usr_david", "usr_priya", "usr_ayesha", "usr_eve"],
            project_id="proj_phoenix",
            scheduled_at=_dt(0, 2),  # In 2 hours
            duration_minutes=15,
            location="Virtual (Google Meet)",
            agenda=["Blockers", "Sprint 44 Burndown", "PR Reviews Pending"],
        ),
        Meeting(
            id="meet_kt_session_arch",
            title="KT Session: Platform Architecture & Microservices Event Stream",
            type=MeetingType.GENERAL,
            description="Knowledge Transfer (KT) walkthrough on the HYPERREALM event bus, Kafka partitions, and data flow.",
            organiser_id="usr_bob",
            attendee_ids=["usr_bob", "usr_priya", "usr_ayesha", "usr_carol", "usr_david"],
            project_id="proj_phoenix",
            scheduled_at=_dt(1, 4),  # Tomorrow
            duration_minutes=60,
            location="Main Tech Boardroom / Virtual",
            agenda=["Architecture Overview", "Event Payload Schemas", "Handling Dead-Letter Queues", "Q&A Session"],
        ),
        Meeting(
            id="meet_kt_session_qa",
            title="KT Session: Automation Quality Gates & Pytest Framework",
            type=MeetingType.GENERAL,
            description="Knowledge Transfer session hosted by QA Lead Priya Sharma explaining our test framework structure.",
            organiser_id="usr_priya",
            attendee_ids=["usr_priya", "usr_ayesha", "usr_eve", "usr_carol"],
            project_id="proj_phoenix",
            scheduled_at=_dt(2, 6),
            duration_minutes=45,
            location="Virtual Lab",
            agenda=["Pytest Fixture Reusability", "Mocking External APIs", "CI Test Reports & Flakiness Triaging"],
        ),
        Meeting(
            id="meet_sprint_44_planning",
            title="Sprint 44 Backlog Planning & Sizing",
            type=MeetingType.SPRINT_PLANNING,
            description="Bi-weekly sprint planning meeting to estimate story points and commit to Sprint 44 goals.",
            organiser_id="usr_henry",
            attendee_ids=["usr_bob", "usr_carol", "usr_priya", "usr_ayesha", "usr_frank", "usr_isabel"],
            project_id="proj_phoenix",
            scheduled_at=_dt(3, 10),
            duration_minutes=90,
            location="Virtual Sprint Room",
            agenda=["Sprint Backlog Review", "Capacity & Velocity Check", "Story Point Estimation", "Sprint Goal Sign-off"],
        ),
        Meeting(
            id="meet_sprint_43_retro",
            title="Sprint 43 Retrospective",
            type=MeetingType.RETROSPECTIVE,
            description="Reviewing team dynamics, pipeline friction, what went well, and actionable improvements.",
            organiser_id="usr_henry",
            attendee_ids=["usr_bob", "usr_carol", "usr_priya", "usr_ayesha", "usr_eve"],
            project_id="proj_phoenix",
            scheduled_at=_dt(-1, 15),
            duration_minutes=60,
            location="Virtual",
            notes="Action: Automated test flakiness in CI was identified as main blocker. Priya & Ayesha assigned to stabilise suite.",
        ),
    ]
    for m in meetings_phase3:
        existing = await meeting_repo.get(m.id)
        if not existing:
            await meeting_repo.create(m)
        else:
            await meeting_repo.update(m)
    print("Seeded meetings & KT sessions")

    # ── 7. Tasks with Deadlines and Overdue Actions (Section A) ─────────────
    tasks_phase3 = [
        # Overdue action for Ayesha
        Task(
            id="task_ayesha_overdue",
            title="Resolve flaky test suite failures on CI staging runner",
            description="Investigate intermittent timeout in auth integration tests. OVERDUE action requiring urgent resolution.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL,
            assignee_id="usr_ayesha",
            reporter_id="usr_priya",
            project_id="proj_phoenix",
            due_date=_dt(-2),  # 2 days overdue!
            tags=["qa", "ci-cd", "overdue", "critical"],
        ),
        # Due today/tomorrow for Ayesha
        Task(
            id="task_ayesha_automation",
            title="Implement automated API contract tests for /api/v1/learning",
            description="Write pytest suite verifying role permissions, prerequisites, and status updates.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id="usr_ayesha",
            reporter_id="usr_priya",
            project_id="proj_phoenix",
            due_date=_dt(1),  # Due tomorrow
            tags=["qa", "testing", "api"],
        ),
        # Pending task for Priya
        Task(
            id="task_priya_qa_governance",
            title="Establish Quality Gate metrics for Sprint 44 release candidate",
            description="Define code coverage threshold (85%) and blocking defect severity criteria.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id="usr_priya",
            reporter_id="usr_bob",
            project_id="proj_phoenix",
            due_date=_dt(3),
            tags=["qa", "governance", "phoenix"],
        ),
        # Task for Carol
        Task(
            id="task_carol_auth_jwt",
            title="Implement JWT refresh token rotation with atomic invalidation",
            description="Secure token rotation mechanism preventing replay attacks on API gateway.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id="usr_carol",
            reporter_id="usr_bob",
            project_id="proj_phoenix",
            due_date=_dt(2),
            tags=["security", "auth", "backend"],
        ),
        # Overdue task for Carol
        Task(
            id="task_carol_api_spec",
            title="Finalize OpenAPI 3.1 documentation for internal microservices",
            description="Align API spec models with Pydantic v2 schemas across all routes.",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            assignee_id="usr_carol",
            reporter_id="usr_bob",
            project_id="proj_phoenix",
            due_date=_dt(-1),  # Overdue by 1 day!
            tags=["docs", "api", "overdue"],
        ),
    ]
    for t in tasks_phase3:
        existing = await task_repo.get(t.id)
        if not existing:
            await task_repo.create(t)
        else:
            await task_repo.update(t)
    print("Seeded tasks")

    # ── 8. Pending Approvals (Section A) ─────────────────────────────────────
    approvals_phase3 = [
        Approval(
            id="appr_ayesha_tooling",
            title="QA Automation Tooling & BrowserStack Cloud License",
            description="Requested by Ayesha Hussain ($450/month) for parallel cross-browser test execution in CI/CD pipeline.",
            requester_id="usr_ayesha",
            approver_id="usr_priya",
            status=ApprovalStatus.PENDING,
            requested_at=_dt(-1),
        ),
        Approval(
            id="appr_priya_security_exp",
            title="Staging Test Certificate Security Exception",
            description="Requested by Priya Sharma: temporary 14-day SSL wildcard cert for automated testing cluster.",
            requester_id="usr_priya",
            approver_id="usr_alice",
            status=ApprovalStatus.PENDING,
            requested_at=_dt(-2),
        ),
        Approval(
            id="appr_carol_remote_leave",
            title="Remote Work Location Adjustment — Carol Adams",
            description="3-month flexible remote work plan for family obligations. Manager reviewed.",
            requester_id="usr_carol",
            approver_id="usr_alice",
            status=ApprovalStatus.PENDING,
            requested_at=_dt(0, -6),
        ),
    ]
    for a in approvals_phase3:
        existing = await approval_repo.get(a.id)
        if not existing:
            await approval_repo.create(a)
        else:
            await approval_repo.update(a)
    print("Seeded approvals")

    # ── 9. Notifications (Section A) ────────────────────────────────────────
    notifications_phase3 = [
        Notification(
            id="notif_ayesha_1",
            user_id="usr_ayesha",
            type=NotificationType.TASK_ASSIGNED,
            title="Urgent Task: Flaky test failures on CI staging",
            body="Priya Sharma assigned you: 'Resolve flaky test suite failures on CI staging runner'",
            link="/app/tasks",
            created_at=_dt(-1),
        ),
        Notification(
            id="notif_ayesha_2",
            user_id="usr_ayesha",
            type=NotificationType.MEETING_REMINDER,
            title="Daily Scrum starts in 2 hours",
            body="Phoenix Squad Daily Scrum scheduled for today at 14:00.",
            link="/app/meetings",
            created_at=_dt(0, -1),
        ),
        Notification(
            id="notif_priya_1",
            user_id="usr_priya",
            type=NotificationType.APPROVAL_REQUESTED,
            title="Approval required: QA Tooling license",
            body="Ayesha Hussain submitted BrowserStack cloud license request ($450/mo).",
            link="/app/tasks",
            created_at=_dt(-1),
        ),
        Notification(
            id="notif_carol_1",
            user_id="usr_carol",
            type=NotificationType.SYSTEM,
            title="Guideline updated: Code Review v2.1",
            body="Code Review Guidelines v2.1 published. Mandatory QA approval now required.",
            link="/app/knowledge",
            created_at=_dt(0, -3),
        ),
    ]
    for n in notifications_phase3:
        await notif_repo.create(n)
    print("Seeded notifications")

    # ── 10. Audit Records & Ingestion Errors (Section D) ─────────────────────
    audit_phase3 = [
        AuditRecord(
            id="audit_ingest_err_1",
            actor_id="usr_alice",
            actor_email="alice.chen@hyperrealm.io",
            action=AuditAction.CREATE,
            resource_type="document_ingestion",
            description="Ingestion failure: Malformed YAML frontmatter in 'draft_kubernetes_policy.md'. Line 14 parse error.",
            metadata={"status": "error", "file": "draft_kubernetes_policy.md", "error_code": "PARSE_ERR_YAML"},
            created_at=_dt(-1, -2),
        ),
        AuditRecord(
            id="audit_ingest_err_2",
            actor_id="usr_frank",
            actor_email="frank.moore@hyperrealm.io",
            action=AuditAction.CREATE,
            resource_type="guideline_ingestion",
            description="Ingestion warning: Missing required owner_id metadata on 'sre_incident_playbook_v2.md'. Defaulted to submitter.",
            metadata={"status": "warning", "file": "sre_incident_playbook_v2.md"},
            created_at=_dt(-2, -5),
        ),
        AuditRecord(
            id="audit_guide_pub_1",
            actor_id="usr_alice",
            actor_email="alice.chen@hyperrealm.io",
            action=AuditAction.UPDATE,
            resource_type="guideline",
            resource_id="guide_code_review",
            description="Published Code Review Guidelines v2.1. Affected teams notified.",
            metadata={"version": "2.1", "status": "published"},
            created_at=_dt(-3),
        ),
        AuditRecord(
            id="audit_auth_fail_1",
            actor_id=None,
            actor_email="external_probe@suspicious.net",
            action=AuditAction.AUTH_FAILURE,
            resource_type="auth",
            description="Multiple failed authentication attempts detected from IP 198.51.100.42",
            ip_address="198.51.100.42",
            created_at=_dt(-1, -8),
        ),
    ]
    for ar in audit_phase3:
        await audit_repo.create(ar)
    print("Seeded audit records and ingestion errors")


if __name__ == "__main__":
    asyncio.run(run_phase3_seed())
