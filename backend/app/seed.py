"""
Seed data for local development and demo.

Populates all repositories with a realistic org hierarchy:

  Engineering Dept
  ├── Alice Chen (Admin / CTO)
  │   ├── Bob Harris (Technical Lead)
  │   │   ├── Carol Adams (Software Developer)
  │   │   ├── David Kim (Software Developer)
  │   │   └── Eve Russo (QA Engineer)
  │   ├── Frank Moore (DevOps Engineer)
  │   └── Grace Liu (Software Developer)
  Product Dept
  ├── Henry Park (Project Manager / Scrum Master)
  │   ├── Isabel Torres (Software Developer)
  │   └── James Wright (QA Engineer)

Projects, tasks, meetings, incidents, learning resources, and notifications
are seeded to give every persona a realistic workspace.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from .auth import hash_password
from .dependencies import (
    get_approval_repo,
    get_audit_repo,
    get_conv_repo,
    get_dept_repo,
    get_guide_repo,
    get_incident_repo,
    get_learning_repo,
    get_meeting_repo,
    get_notif_repo,
    get_project_repo,
    get_task_repo,
    get_user_repo,
    get_doc_repo,
)
from .models import (
    Approval,
    ApprovalStatus,
    AuditAction,
    AuditRecord,
    Conversation,
    Department,
    Document,
    Guideline,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    LearningResource,
    Meeting,
    MeetingType,
    Message,
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
    LearningStatus,
    utcnow,
)


_NOW = datetime(2026, 10, 15, 12, 0, 0)

def _dt(days: int = 0, hours: int = 0) -> datetime:
    return _NOW + timedelta(days=days, hours=hours)


async def seed_all() -> None:
    """Run all seeders in order. Safe to call after repositories are initialised."""

    user_repo = get_user_repo()
    dept_repo = get_dept_repo()
    project_repo = get_project_repo()
    conv_repo = get_conv_repo()
    doc_repo = get_doc_repo()
    guide_repo = get_guide_repo()
    learning_repo = get_learning_repo()
    meeting_repo = get_meeting_repo()
    task_repo = get_task_repo()
    approval_repo = get_approval_repo()
    incident_repo = get_incident_repo()
    notif_repo = get_notif_repo()
    audit_repo = get_audit_repo()

    # Check if database is already seeded
    existing = await user_repo.get_by_email("alice.chen@hyperrealm.io")
    if existing:
        print("[OK] Database already seeded, skipping seed")
        return

    # ── Departments ──────────────────────────────────────────────────────────

    eng_dept = Department(
        id="dept_engineering",
        name="Engineering",
        description="Software engineering, DevOps, and QA",
    )
    prod_dept = Department(
        id="dept_product",
        name="Product",
        description="Product management and business analysis",
    )
    for d in (eng_dept, prod_dept):
        await dept_repo.create(d)

    # ── Users ────────────────────────────────────────────────────────────────

    pw = hash_password("Password123!")  # shared demo password

    alice = UserProfile(
        id="usr_alice",
        email="alice.chen@hyperrealm.io",
        name="Alice Chen",
        role=UserRole.ADMIN,
        department_id="dept_engineering",
        department_name="Engineering",
        job_title="CTO",
        manager_id=None,
        hashed_password=pw,
        skills=["Leadership", "Architecture", "Cloud"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-180),
    )

    bob = UserProfile(
        id="usr_bob",
        email="bob.harris@hyperrealm.io",
        name="Bob Harris",
        role=UserRole.TECHNICAL_LEAD,
        department_id="dept_engineering",
        department_name="Engineering",
        job_title="Technical Lead",
        manager_id="usr_alice",
        hashed_password=pw,
        skills=["Python", "FastAPI", "System Design", "Code Review"],
        project_ids=["proj_phoenix", "proj_sentinel"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-150),
    )

    carol = UserProfile(
        id="usr_carol",
        email="carol.adams@hyperrealm.io",
        name="Carol Adams",
        role=UserRole.SOFTWARE_DEVELOPER,
        department_id="dept_engineering",
        department_name="Engineering",
        job_title="Senior Software Developer",
        manager_id="usr_bob",
        hashed_password=pw,
        skills=["React", "TypeScript", "Python", "FastAPI"],
        project_ids=["proj_phoenix"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-120),
    )

    david = UserProfile(
        id="usr_david",
        email="david.kim@hyperrealm.io",
        name="David Kim",
        role=UserRole.SOFTWARE_DEVELOPER,
        department_id="dept_engineering",
        department_name="Engineering",
        job_title="Software Developer",
        manager_id="usr_bob",
        hashed_password=pw,
        skills=["Python", "Django", "PostgreSQL", "Docker"],
        project_ids=["proj_sentinel"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-90),
    )

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
        skills=["Quality Strategy", "Test Architecture", "Python Automation", "CI/CD Gates"],
        project_ids=["proj_phoenix", "proj_sentinel"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-140),
    )

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
        skills=["Python Automation", "Pytest", "API Testing", "Postman", "Defect Management"],
        project_ids=["proj_phoenix"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-80),
    )

    eve = UserProfile(
        id="usr_eve",
        email="eve.russo@hyperrealm.io",
        name="Eve Russo",
        role=UserRole.QA_ENGINEER,
        department_id="dept_engineering",
        department_name="Engineering",
        job_title="Senior QA Engineer",
        manager_id="usr_priya",
        hashed_password=pw,
        skills=["Pytest", "Selenium", "Test Planning", "CI/CD"],
        project_ids=["proj_phoenix", "proj_sentinel"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-60),
    )

    frank = UserProfile(
        id="usr_frank",
        email="frank.moore@hyperrealm.io",
        name="Frank Moore",
        role=UserRole.DEVOPS_ENGINEER,
        department_id="dept_engineering",
        department_name="Engineering",
        job_title="DevOps Engineer",
        manager_id="usr_alice",
        hashed_password=pw,
        skills=["Kubernetes", "Terraform", "GCP", "CI/CD", "Docker"],
        project_ids=["proj_phoenix", "proj_sentinel"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-100),
    )

    grace = UserProfile(
        id="usr_grace",
        email="grace.liu@hyperrealm.io",
        name="Grace Liu",
        role=UserRole.SOFTWARE_DEVELOPER,
        department_id="dept_engineering",
        department_name="Engineering",
        job_title="Software Developer",
        manager_id="usr_alice",
        hashed_password=pw,
        skills=["Go", "gRPC", "Microservices"],
        project_ids=["proj_sentinel"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-50),
    )

    henry = UserProfile(
        id="usr_henry",
        email="henry.park@hyperrealm.io",
        name="Henry Park",
        role=UserRole.PROJECT_MANAGER,
        department_id="dept_product",
        department_name="Product",
        job_title="Project Manager / Scrum Master",
        manager_id="usr_alice",
        hashed_password=pw,
        skills=["Agile", "Scrum", "Jira", "Stakeholder Management"],
        project_ids=["proj_phoenix"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-130),
    )

    isabel = UserProfile(
        id="usr_isabel",
        email="isabel.torres@hyperrealm.io",
        name="Isabel Torres",
        role=UserRole.SOFTWARE_DEVELOPER,
        department_id="dept_product",
        department_name="Product",
        job_title="Software Developer",
        manager_id="usr_henry",
        hashed_password=pw,
        skills=["Vue.js", "Node.js", "MongoDB"],
        project_ids=["proj_phoenix"],
        status=UserStatus.ACTIVE,
        created_at=_dt(-30),
    )

    james = UserProfile(
        id="usr_james",
        email="james.wright@hyperrealm.io",
        name="James Wright",
        role=UserRole.QA_ENGINEER,
        department_id="dept_product",
        department_name="Product",
        job_title="QA Engineer",
        manager_id="usr_henry",
        hashed_password=pw,
        skills=["Cypress", "Playwright", "API Testing"],
        project_ids=["proj_phoenix"],
        status=UserStatus.PENDING,
        created_at=_dt(-7),
    )

    users = [alice, bob, priya, ayesha, carol, david, eve, frank, grace, henry, isabel, james]
    for u in users:
        await user_repo.create(u)

    # Update dept heads
    eng_dept.head_user_id = "usr_alice"
    prod_dept.head_user_id = "usr_henry"
    await dept_repo.update(eng_dept)
    await dept_repo.update(prod_dept)

    # ── Projects ─────────────────────────────────────────────────────────────

    phoenix = Project(
        id="proj_phoenix",
        name="Project Phoenix",
        description="Next-generation enterprise AI platform — HYPERREALM v2",
        status=ProjectStatus.ACTIVE,
        owner_id="usr_bob",
        member_ids=["usr_carol", "usr_eve", "usr_frank", "usr_henry", "usr_isabel", "usr_james"],
        department_id="dept_engineering",
        tags=["AI", "Platform", "Priority"],
        start_date=_dt(-90),
        end_date=_dt(90),
    )

    sentinel = Project(
        id="proj_sentinel",
        name="Project Sentinel",
        description="Security and compliance monitoring pipeline",
        status=ProjectStatus.ACTIVE,
        owner_id="usr_alice",
        member_ids=["usr_bob", "usr_david", "usr_eve", "usr_frank", "usr_grace"],
        department_id="dept_engineering",
        tags=["Security", "Compliance", "Infrastructure"],
        start_date=_dt(-60),
        end_date=_dt(60),
    )

    for p in (phoenix, sentinel):
        await project_repo.create(p)

    # ── Documents ────────────────────────────────────────────────────────────

    docs = [
        Document(
            id="doc_remote_policy",
            title="Remote Work Policy v3.2",
            content=(
                "# Remote Work Policy\n\n"
                "## Eligibility\nAll full-time employees with > 6 months tenure.\n\n"
                "## Core Hours\nEmployees must be available 10:00–15:00 local time.\n\n"
                "## Approval Process\n1. Submit request to direct manager\n"
                "2. HR review within 5 business days\n3. CTO sign-off for > 3 months."
            ),
            category="hr",
            tags=["remote", "policy", "hr"],
            author_id="usr_alice",
            department_id=None,
            is_public=True,
            created_at=_dt(-30),
        ),
        Document(
            id="doc_security_guide",
            title="Security Guidelines 2026",
            content=(
                "# Security Guidelines\n\n"
                "## Access Control\n- Least-privilege principle enforced.\n"
                "- MFA mandatory for all accounts.\n\n"
                "## Incident Reporting\nReport via the Incidents portal within 1 hour of detection.\n\n"
                "## Code Security\n- No secrets in source code.\n"
                "- Dependency scans on every PR."
            ),
            category="security",
            tags=["security", "compliance", "mfa"],
            author_id="usr_frank",
            department_id="dept_engineering",
            is_public=True,
            created_at=_dt(-45),
        ),
        Document(
            id="doc_api_standards",
            title="API Design Standards",
            content=(
                "# API Design Standards\n\n"
                "## REST Conventions\n- Use nouns for resources.\n"
                "- Version APIs via URL prefix `/v1/`.\n\n"
                "## Error Handling\n- Always return RFC 7807 Problem Details.\n\n"
                "## Pagination\n- Cursor or offset-based, max 100 items per page."
            ),
            category="engineering",
            tags=["api", "standards", "rest"],
            author_id="usr_bob",
            department_id="dept_engineering",
            is_public=True,
            created_at=_dt(-20),
        ),
    ]
    for doc in docs:
        await doc_repo.create(doc)

    # ── Guidelines ───────────────────────────────────────────────────────────

    guidelines = [
        Guideline(
            id="guide_code_review",
            title="Code Review Guidelines",
            content=(
                "All PRs require at least one approving review from a peer "
                "and a final sign-off from the Technical Lead. PRs > 400 lines "
                "must be split. Test coverage must not drop below 80%."
            ),
            category="engineering",
            owner_id="usr_bob",
            tags=["code-review", "quality"],
            created_at=_dt(-60),
        ),
        Guideline(
            id="guide_incident_response",
            title="Incident Response Runbook",
            content=(
                "P1 incidents: page on-call within 5 minutes, bridge call within 15. "
                "P2: notify team within 30 minutes. "
                "All incidents require a post-mortem within 5 business days."
            ),
            category="security",
            owner_id="usr_frank",
            tags=["incident", "runbook", "sre"],
            created_at=_dt(-90),
        ),
        Guideline(
            id="guide_agile",
            title="Agile & Scrum Playbook",
            content=(
                "Two-week sprints. Daily standups at 09:30. "
                "Sprint planning: first Monday. Review + Retro: last Friday. "
                "Definition of Done: code reviewed, tested, deployed to staging, "
                "acceptance criteria verified."
            ),
            category="process",
            owner_id="usr_henry",
            tags=["agile", "scrum", "process"],
            created_at=_dt(-45),
        ),
    ]
    for g in guidelines:
        await guide_repo.create(g)

    # ── Learning resources ────────────────────────────────────────────────────

    resources = [
        LearningResource(
            id="learn_fastapi",
            title="FastAPI Deep Dive",
            description="Async Python APIs with FastAPI, Pydantic v2, and SQLAlchemy.",
            category="engineering",
            url="https://fastapi.tiangolo.com/tutorial/",
            estimated_minutes=240,
            required_for_roles=[UserRole.SOFTWARE_DEVELOPER, UserRole.TECHNICAL_LEAD],
            tags=["python", "fastapi", "backend"],
        ),
        LearningResource(
            id="learn_react_arch",
            title="React Architecture Patterns",
            description="Component design, state management, and performance.",
            category="engineering",
            url="https://react.dev/learn",
            estimated_minutes=180,
            required_for_roles=[UserRole.SOFTWARE_DEVELOPER],
            tags=["react", "frontend", "typescript"],
        ),
        LearningResource(
            id="learn_security",
            title="Security Fundamentals for Engineers",
            description="OWASP Top 10, secure coding practices, and threat modelling.",
            category="security",
            url="https://owasp.org/www-project-top-ten/",
            estimated_minutes=120,
            required_for_roles=[UserRole.SOFTWARE_DEVELOPER, UserRole.QA_ENGINEER, UserRole.DEVOPS_ENGINEER],
            tags=["security", "owasp"],
        ),
        LearningResource(
            id="learn_incident",
            title="Incident Response & SRE Basics",
            description="SLO/SLI concepts, blameless post-mortems, on-call runbooks.",
            category="devops",
            url="https://sre.google/books/",
            estimated_minutes=90,
            required_for_roles=[UserRole.DEVOPS_ENGINEER, UserRole.TECHNICAL_LEAD],
            tags=["sre", "incident", "reliability"],
        ),
        LearningResource(
            id="learn_agile",
            title="Agile & Scrum Certification Prep",
            description="Scrum framework, ceremonies, and scaled Agile.",
            category="process",
            estimated_minutes=150,
            required_for_roles=[UserRole.PROJECT_MANAGER],
            tags=["agile", "scrum", "psm"],
        ),
        LearningResource(
            id="learn_k8s",
            title="Kubernetes for Production",
            description="Cluster management, Helm, networking, and autoscaling.",
            category="devops",
            estimated_minutes=300,
            required_for_roles=[UserRole.DEVOPS_ENGINEER],
            tags=["kubernetes", "k8s", "docker"],
        ),
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

        # New Employee
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
    for r in resources:
        await learning_repo.create_resource(r)

    # Learning progress for Carol
    carol_progress = [
        UserLearningProgress(
            id="ulp_carol_react",
            user_id="usr_carol",
            resource_id="learn_react_arch",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=72,
            started_at=_dt(-14),
        ),
        UserLearningProgress(
            id="ulp_carol_security",
            user_id="usr_carol",
            resource_id="learn_security",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=45,
            started_at=_dt(-7),
        ),
        UserLearningProgress(
            id="ulp_carol_fastapi",
            user_id="usr_carol",
            resource_id="learn_fastapi",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-40),
            completed_at=_dt(-10),
        ),
    ]
    for p in carol_progress:
        await learning_repo.upsert_progress(p)

    # Learning progress for Frank
    frank_progress = [
        UserLearningProgress(
            id="ulp_frank_k8s",
            user_id="usr_frank",
            resource_id="learn_k8s",
            status=LearningStatus.IN_PROGRESS,
            progress_pct=65,
            started_at=_dt(-21),
        ),
        UserLearningProgress(
            id="ulp_frank_incident",
            user_id="usr_frank",
            resource_id="learn_incident",
            status=LearningStatus.COMPLETED,
            progress_pct=100,
            started_at=_dt(-60),
            completed_at=_dt(-30),
        ),
    ]
    for p in frank_progress:
        await learning_repo.upsert_progress(p)

    # ── Meetings ─────────────────────────────────────────────────────────────

    meetings = [
        Meeting(
            id="meet_standup_1",
            title="Daily Standup — Phoenix Team",
            type=MeetingType.STANDUP,
            description="15-minute sync on daily progress and blockers.",
            organiser_id="usr_henry",
            attendee_ids=["usr_bob", "usr_carol", "usr_david", "usr_eve", "usr_isabel"],
            project_id="proj_phoenix",
            scheduled_at=_dt(1, 9),
            duration_minutes=15,
            agenda=["What did you do yesterday?", "What will you do today?", "Any blockers?"],
        ),
        Meeting(
            id="meet_sprint_planning",
            title="Sprint 44 Planning",
            type=MeetingType.SPRINT_PLANNING,
            description="Plan Sprint 44 backlog and assign story points.",
            organiser_id="usr_henry",
            attendee_ids=["usr_bob", "usr_carol", "usr_david", "usr_eve", "usr_frank", "usr_isabel"],
            project_id="proj_phoenix",
            scheduled_at=_dt(3, 10),
            duration_minutes=120,
            agenda=["Backlog review", "Capacity planning", "Story point estimation", "Sprint goal"],
        ),
        Meeting(
            id="meet_retro",
            title="Sprint 43 Retrospective",
            type=MeetingType.RETROSPECTIVE,
            description="What went well, what to improve, action items.",
            organiser_id="usr_henry",
            attendee_ids=["usr_bob", "usr_carol", "usr_eve"],
            project_id="proj_phoenix",
            scheduled_at=_dt(-1, 14),
            duration_minutes=60,
            notes=(
                "Went well: CI/CD pipeline improvements.\n"
                "Improve: PR review turnaround time.\n"
                "Action: Bob to define PR review SLA by next sprint."
            ),
        ),
        Meeting(
            id="meet_1on1_alice_bob",
            title="1:1 — Alice & Bob",
            type=MeetingType.ONE_ON_ONE,
            organiser_id="usr_alice",
            attendee_ids=["usr_bob"],
            scheduled_at=_dt(2, 15),
            duration_minutes=30,
            agenda=["Career development", "Project Phoenix blockers", "Team health"],
        ),
        Meeting(
            id="meet_incident_review",
            title="INC-0241 Post-mortem",
            type=MeetingType.REVIEW,
            description="Post-mortem for the authentication service outage.",
            organiser_id="usr_frank",
            attendee_ids=["usr_alice", "usr_bob", "usr_david"],
            project_id="proj_sentinel",
            scheduled_at=_dt(4, 11),
            duration_minutes=90,
            agenda=["Timeline review", "Root cause analysis", "Preventive measures"],
        ),
    ]
    for m in meetings:
        await meeting_repo.create(m)

    # ── Tasks ────────────────────────────────────────────────────────────────

    tasks = [
        Task(
            id="task_auth_service",
            title="Implement JWT refresh token rotation",
            description="Add refresh token support to the auth service with rotation on use.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id="usr_carol",
            reporter_id="usr_bob",
            project_id="proj_phoenix",
            due_date=_dt(5),
            tags=["auth", "security"],
        ),
        Task(
            id="task_api_pagination",
            title="Add pagination to all list endpoints",
            description="Implement cursor-based pagination across all API endpoints.",
            status=TaskStatus.IN_REVIEW,
            priority=TaskPriority.MEDIUM,
            assignee_id="usr_david",
            reporter_id="usr_bob",
            project_id="proj_phoenix",
            due_date=_dt(3),
            tags=["api", "backend"],
        ),
        Task(
            id="task_ci_pipeline",
            title="Set up GitHub Actions CI pipeline",
            description="Configure lint, test, build, and deploy stages for all services.",
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
            assignee_id="usr_frank",
            reporter_id="usr_alice",
            project_id="proj_phoenix",
            due_date=_dt(-5),
            tags=["devops", "ci-cd"],
        ),
        Task(
            id="task_e2e_tests",
            title="Write E2E test suite for auth flow",
            description="Playwright tests covering login, token refresh, and logout.",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            assignee_id="usr_eve",
            reporter_id="usr_bob",
            project_id="proj_phoenix",
            due_date=_dt(7),
            tags=["testing", "e2e"],
        ),
        Task(
            id="task_sentinel_monitoring",
            title="Deploy Prometheus + Grafana dashboards",
            description="Set up observability stack for Sentinel microservices.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL,
            assignee_id="usr_frank",
            reporter_id="usr_alice",
            project_id="proj_sentinel",
            due_date=_dt(2),
            tags=["monitoring", "devops", "sentinel"],
        ),
        Task(
            id="task_onboarding_james",
            title="Complete James's onboarding checklist",
            description="30-day onboarding tasks for James Wright — QA Engineer.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            assignee_id="usr_james",
            reporter_id="usr_henry",
            project_id="proj_phoenix",
            due_date=_dt(23),
            tags=["onboarding", "hr"],
        ),
        Task(
            id="task_doc_update",
            title="Update API documentation for v2 endpoints",
            description="Ensure all new v2 endpoints are documented in OpenAPI spec.",
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            assignee_id="usr_carol",
            reporter_id="usr_bob",
            project_id="proj_phoenix",
            due_date=_dt(14),
            tags=["docs", "api"],
        ),
    ]
    for t in tasks:
        await task_repo.create(t)

    # ── Approvals ────────────────────────────────────────────────────────────

    approvals = [
        Approval(
            id="appr_q4_tooling",
            title="Q4 Engineering Tooling Budget",
            description="$12,000 for JetBrains licenses, SonarCloud, and DataDog.",
            requester_id="usr_bob",
            approver_id="usr_alice",
            status=ApprovalStatus.PENDING,
            requested_at=_dt(-2),
        ),
        Approval(
            id="appr_remote_carol",
            title="Remote Work Extension — Carol Adams",
            description="Requesting 3-month remote extension for personal reasons.",
            requester_id="usr_carol",
            approver_id="usr_alice",
            status=ApprovalStatus.PENDING,
            requested_at=_dt(-1),
        ),
        Approval(
            id="appr_cloud_upgrade",
            title="GCP Quota Increase — Sentinel Project",
            description="Request to increase Cloud Run quota for Sentinel services.",
            requester_id="usr_frank",
            approver_id="usr_alice",
            status=ApprovalStatus.APPROVED,
            decision_note="Approved. Stay within monthly budget cap.",
            requested_at=_dt(-10),
            resolved_at=_dt(-8),
        ),
    ]
    for a in approvals:
        await approval_repo.create(a)

    # ── Incidents ────────────────────────────────────────────────────────────

    incidents = [
        Incident(
            id="inc_0241",
            title="Authentication Service Outage — 2026-10-12",
            description=(
                "The auth service crashed due to a memory leak in the token cache. "
                "Affected all API consumers for ~35 minutes."
            ),
            severity=IncidentSeverity.P2,
            status=IncidentStatus.RESOLVED,
            reporter_id="usr_frank",
            assignee_id="usr_david",
            project_id="proj_sentinel",
            tags=["auth", "memory", "outage"],
            resolution_notes="Patched cache eviction logic. Deployed hotfix v1.2.3.",
            created_at=_dt(-3),
            resolved_at=_dt(-3, 1),
        ),
        Incident(
            id="inc_0242",
            title="Elevated 5xx Error Rate — Phoenix API Gateway",
            description="Error rate spiked to 8% on /api/v1/conversations endpoint.",
            severity=IncidentSeverity.P3,
            status=IncidentStatus.INVESTIGATING,
            reporter_id="usr_eve",
            assignee_id="usr_carol",
            project_id="proj_phoenix",
            tags=["api", "error-rate"],
            created_at=_dt(0, -2),
        ),
        Incident(
            id="inc_0243",
            title="Dependency Vulnerability — CVE-2026-XXXXX",
            description="Critical vulnerability found in `requests` library < 2.32.",
            severity=IncidentSeverity.P1,
            status=IncidentStatus.OPEN,
            reporter_id="usr_frank",
            assignee_id="usr_frank",
            project_id="proj_sentinel",
            tags=["security", "cve", "dependency"],
            created_at=_dt(0, -1),
        ),
    ]
    for i in incidents:
        await incident_repo.create(i)

    # ── Notifications ────────────────────────────────────────────────────────

    notifications = [
        Notification(
            id="notif_1",
            user_id="usr_alice",
            type=NotificationType.APPROVAL_REQUESTED,
            title="New approval request",
            body="Bob Harris has submitted a Q4 tooling budget request for your review.",
            link="/app/tasks",
            created_at=_dt(-2),
        ),
        Notification(
            id="notif_2",
            user_id="usr_carol",
            type=NotificationType.TASK_ASSIGNED,
            title="New task assigned",
            body="Bob Harris assigned you: 'Implement JWT refresh token rotation'",
            link="/app/tasks",
            created_at=_dt(-1),
        ),
        Notification(
            id="notif_3",
            user_id="usr_frank",
            type=NotificationType.INCIDENT_CREATED,
            title="P1 Incident — CVE-2026-XXXXX",
            body="A critical dependency vulnerability requires immediate attention.",
            link="/app/tasks",
            created_at=_dt(0, -1),
        ),
        Notification(
            id="notif_4",
            user_id="usr_bob",
            type=NotificationType.MEETING_REMINDER,
            title="Sprint 44 Planning in 1 hour",
            body="Sprint 44 Planning starts at 10:00. Please join the video call.",
            link="/app/meetings",
            created_at=_dt(3, 9),
        ),
        Notification(
            id="notif_5",
            user_id="usr_alice",
            type=NotificationType.APPROVAL_REQUESTED,
            title="Remote work extension request",
            body="Carol Adams has requested a 3-month remote extension.",
            link="/app/tasks",
            created_at=_dt(-1),
        ),
    ]
    for n in notifications:
        await notif_repo.create(n)

    # ── Audit records ────────────────────────────────────────────────────────

    audit_records = [
        AuditRecord(
            id="audit_1",
            actor_id="usr_alice",
            actor_email="alice.chen@hyperrealm.io",
            action=AuditAction.LOGIN,
            resource_type="session",
            description="Successful login",
            created_at=_dt(0, -3),
        ),
        AuditRecord(
            id="audit_2",
            actor_id="usr_frank",
            actor_email="frank.moore@hyperrealm.io",
            action=AuditAction.CREATE,
            resource_type="incident",
            resource_id="inc_0243",
            description="Created P1 incident: CVE-2026-XXXXX",
            created_at=_dt(0, -1),
        ),
        AuditRecord(
            id="audit_3",
            actor_id="usr_bob",
            actor_email="bob.harris@hyperrealm.io",
            action=AuditAction.CREATE,
            resource_type="approval",
            resource_id="appr_q4_tooling",
            description="Submitted Q4 tooling budget approval",
            created_at=_dt(-2),
        ),
        AuditRecord(
            id="audit_4",
            actor_id="usr_alice",
            actor_email="alice.chen@hyperrealm.io",
            action=AuditAction.UPDATE,
            resource_type="approval",
            resource_id="appr_cloud_upgrade",
            description="Approved GCP quota increase request",
            created_at=_dt(-8),
        ),
    ]
    for r in audit_records:
        await audit_repo.create(r)

    # ── Sample conversations & messages ───────────────────────────────────────

    conv1 = Conversation(
        id="conv_demo_1",
        user_id="usr_carol",
        title="Q3 incident analysis",
        agent_id="insights",
        created_at=_dt(-2),
    )
    await conv_repo.create(conv1)
    await conv_repo.add_message(Message(
        id="msg_demo_1",
        conversation_id="conv_demo_1",
        role="user",
        content="Summarise the Q3 incident report and highlight recurring patterns",
        created_at=_dt(-2),
    ))
    await conv_repo.add_message(Message(
        id="msg_demo_2",
        conversation_id="conv_demo_1",
        role="assistant",
        agent_id="insights",
        content=(
            "**Q3 Incident Summary**\n\n"
            "In Q3 we recorded **7 incidents** (2x P1, 3x P2, 2x P3).\n\n"
            "**Recurring patterns:**\n"
            "- 57% related to memory management in Python services\n"
            "- 43% involved cache invalidation failures\n"
            "- Average resolution time: 2h 15m (target: < 2h)\n\n"
            "**Recommendations:**\n"
            "1. Add memory profiling to CI pipeline\n"
            "2. Review caching strategy for auth tokens\n"
            "3. Set up automated alerting at 70% memory usage threshold"
        ),
        created_at=_dt(-2, 0),
    ))

    print("[OK] Seed data loaded successfully")


if __name__ == "__main__":
    asyncio.run(seed_all())

