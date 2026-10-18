"""
Phase 04 seed script.
Seeds official authoritative guidelines (Brand Identity v2.1, Engineering Security v3.0),
guideline versions, employee personal KT documents, historical incidents,
and sample brand-compliance reports.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from .dependencies import (
    get_act_repo,
    get_bcr_repo,
    get_doc_repo,
    get_guide_repo,
    get_gver_repo,
    get_incident_repo,
    get_user_repo,
    init_repositories,
)
from .models import (
    ActionExecutionRecord,
    ActionStatus,
    BrandComplianceReport,
    ComplianceStatus,
    Document,
    DocumentScope,
    Guideline,
    GuidelineStatus,
    GuidelineVersionRecord,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    ProcessingStatus,
    utcnow,
)

_NOW = datetime.utcnow()


def _dt(days: int = 0, hours: int = 0) -> datetime:
    return _NOW + timedelta(days=days, hours=hours)


async def run_phase4_seed():
    init_repositories()

    guide_repo = get_guide_repo()
    gver_repo = get_gver_repo()
    doc_repo = get_doc_repo()
    inc_repo = get_incident_repo()
    bcr_repo = get_bcr_repo()
    user_repo = get_user_repo()

    # Find admin user (Alice Chen usr_alice or Bob Harris usr_bob)
    admin = await user_repo.get_by_email("alice.chen@hyperrealm.io")
    admin_id = admin.id if admin else "usr_alice"

    # ── 1. Official Authoritative Brand Guidelines (v2.1) ──────────────────────
    brand_content = (
        "# HYPERREALM Brand Identity & Design Standards v2.1\n\n"
        "## §1 Scope & Authority\n"
        "These brand guidelines are authoritative across all digital and print materials produced by or for HYPERREALM. "
        "Any external or public-facing visual asset must strictly adhere to these standards.\n\n"
        "## §2 Color Tokens & Palette\n"
        "- **Primary Accent (Hyper Indigo):** `#6366F1` (RGB: 99, 102, 241). Minimum contrast against dark backgrounds: 4.5:1.\n"
        "- **Deep Indigo Brand:** `#4F46E5` (RGB: 79, 70, 229).\n"
        "- **Dark Mode Background:** `#0B0F19` (Canvas) and `#0F172A` (Elevated Card).\n"
        "- **Light Mode Background:** `#FFFFFF` (Surface) and `#F8FAFC` (Canvas).\n"
        "- **Text Primary:** `#F8FAFC` (Dark mode) / `#0F172A` (Light mode).\n"
        "- **Text Secondary:** `#94A3B8` (Dark mode) / `#64748B` (Light mode).\n"
        "- **Prohibited:** Unapproved neon greens (#10B981 on non-status elements), unapproved high-saturation reds, or harsh rainbows.\n\n"
        "## §3 Logo Placement & Protection Zone\n"
        "- **Clear Space:** The HYPERREALM logo mark must maintain a minimum clear space buffer of 24px (1.5rem) on all four borders.\n"
        "- **Proportions:** The aspect ratio of the geometric mark must remain exactly 1:1. No squashing, stretching, or skewing.\n"
        "- **Placement:** Primary placement is top-left header or optically centered hero lockup.\n"
        "- **Prohibited:** Do not apply drop shadows, emboss effects, or unapproved color gradients to the standalone icon.\n\n"
        "## §4 Typography\n"
        "- **Display & Headings:** `Outfit` (sans-serif), font weights 600 or 700.\n"
        "- **Body & UI Elements:** `Inter` (sans-serif), font weights 400 or 500.\n"
        "- **Contrast Ratio:** Text-to-background contrast ratio must satisfy WCAG AA (minimum 4.5:1 for normal text, 3:1 for large text).\n\n"
        "## §5 Disclaimers & Legal Requirements\n"
        "- **Internal Materials:** All enterprise slides, mockups, and presentations must feature the disclaimer: 'Confidential - Hyperrealm Internal' in the footer margin."
    )

    brand_guide = await guide_repo.get("guide_brand_identity")
    if not brand_guide:
        brand_guide = Guideline(
            id="guide_brand_identity",
            title="Hyperrealm Brand Identity & Design Standards",
            content=brand_content,
            description="Authoritative visual identity, color tokens, logo protection rules, and typography hierarchy.",
            category="brand",
            owner_id=admin_id,
            version="2.1",
            status="published",
            effective_date=_dt(-60),
            changelog="Updated color tokens for WCAG AA 4.5:1 contrast and added clear space requirement (24px).",
            applicable_roles=["admin", "technical_lead", "software_developer", "qa_engineer", "project_manager", "employee"],
            applicable_departments=["Engineering", "Design", "Product", "Marketing"],
            processing_status=ProcessingStatus.INDEXED,
            created_at=_dt(-120),
            updated_at=_dt(-60),
        )
        await guide_repo.create(brand_guide)

    # Seed previous version (v2.0) in guideline_versions
    prev_v20 = await gver_repo.get("gver_brand_2_0")
    if not prev_v20:
        await gver_repo.create(
            GuidelineVersionRecord(
                id="gver_brand_2_0",
                guideline_id="guide_brand_identity",
                version="2.0",
                title="Hyperrealm Brand Identity Guidelines v2.0",
                content="# HYPERREALM Brand Identity Guidelines v2.0\nInitial color token definitions with 16px logo clear space.",
                description="Initial brand rollout version.",
                category="brand",
                changelog="Initial release across organization.",
                status="archived",
                created_by=admin_id,
                effective_date=_dt(-180),
                created_at=_dt(-180),
            )
        )

    # ── 2. Official Authoritative Security & Coding Standards (v3.0) ───────────
    sec_content = (
        "# HYPERREALM Engineering Security & Zero Trust Architecture Standards v3.0\n\n"
        "## §1 Authentication & Token Lifecycle\n"
        "- **Protocol:** All client-to-server communications must authenticate using OAuth 2.0 with PKCE.\n"
        "- **Tokens:** JWT access tokens must have a maximum lifetime of 60 minutes.\n"
        "- **Storage Policy:** Refresh tokens and access tokens MUST be stored in Secure, HTTP-only, SameSite=Strict cookies. "
        "Storing tokens in client-side localStorage or unencrypted indexedDB is strictly forbidden due to XSS vulnerability exposure.\n"
        "- **Revocation:** Rotating refresh tokens must revoke the previous family token immediately upon detection of reuse.\n\n"
        "## §2 Quality Gates & Deployment\n"
        "- All commits to main branch require passing automated regression test suites with >= 85% coverage."
    )

    sec_guide = await guide_repo.get("guide_security_standards")
    if not sec_guide:
        sec_guide = Guideline(
            id="guide_security_standards",
            title="Engineering Security & Zero Trust Architecture Standards",
            content=sec_content,
            description="Authoritative cybersecurity architecture, OAuth token policies, and HTTP-only cookie rules.",
            category="security",
            owner_id=admin_id,
            version="3.0",
            status="published",
            effective_date=_dt(-30),
            changelog="Mandated HTTP-only SameSite cookie storage and prohibited client localStorage token persistence.",
            applicable_roles=["admin", "technical_lead", "software_developer", "devops_engineer", "qa_engineer"],
            applicable_departments=["Engineering"],
            processing_status=ProcessingStatus.INDEXED,
            created_at=_dt(-90),
            updated_at=_dt(-30),
        )
        await guide_repo.create(sec_guide)

    # Seed previous version (v2.0) for security standards
    prev_sec20 = await gver_repo.get("gver_sec_2_0")
    if not prev_sec20:
        sec_v20_content = (
            "# HYPERREALM Engineering Security & Architecture Standards v2.0\n\n"
            "## §1 Authentication & Token Lifecycle\n"
            "- **Protocol:** Client-to-server communications may authenticate using standard Bearer OAuth 2.0 tokens.\n"
            "- **Tokens:** JWT access tokens have a maximum lifetime of 120 minutes.\n"
            "- **Storage Policy:** Refresh tokens and access tokens can be stored in browser localStorage or sessionStorage "
            "for persistent client single-page application sessions.\n"
            "- **Revocation:** Refresh tokens are revoked upon manual user signout.\n\n"
            "## §2 Quality Gates & Deployment\n"
            "- Commits to develop branch require code review and unit tests passing with >= 70% coverage."
        )
        await gver_repo.create(
            GuidelineVersionRecord(
                id="gver_sec_2_0",
                guideline_id="guide_security_standards",
                version="2.0",
                title="Engineering Security & Architecture Standards v2.0",
                content=sec_v20_content,
                description="Legacy security architecture prior to zero-trust HTTP-only cookie lockdown.",
                category="security",
                changelog="Permitted browser localStorage token caching and 120-minute expiry.",
                status="archived",
                created_by=admin_id,
                effective_date=_dt(-90),
                created_at=_dt(-90),
            )
        )

    # ── 3. Personal Employee KT Documents (User Knowledge Hubs) ───────────────
    # Alice's Payments API KT Document
    alice_payments = await doc_repo.get("doc_payments_kt")
    if not alice_payments:
        alice_payments = Document(
            id="doc_payments_kt",
            title="Payments Gateway API Integration & Auth KT",
            content=(
                "Payments Gateway API Integration Guide.\n\n"
                "Overview:\n"
                "The payments processing subsystem connects with Stripe and Adyen webhooks via an asynchronous event queue.\n\n"
                "Authentication Module:\n"
                "Incoming webhook notifications authenticate using HMAC-SHA256 signatures passed in the 'X-Signature-SHA256' header. "
                "The authentication module verifies the signature using the pre-shared webhook secret key before deserializing the event payload.\n\n"
                "Token Handling:\n"
                "Our client service initiates payment intents via OAuth2 bearer tokens cached in Redis for 45 minutes.\n\n"
                "Troubleshooting:\n"
                "If webhook verification fails with 401 Unauthorized, ensure the secret key in Secrets Manager is synchronized."
            ),
            category="kt",
            tags=["payments", "auth", "api", "architecture"],
            author_id="usr_alice",
            department_id="dept_engineering",
            is_public=False,
            scope=DocumentScope.PERSONAL,
            file_type="txt",
            file_size=1024,
            status=ProcessingStatus.INDEXED,
            version=1,
            created_at=_dt(-14),
            updated_at=_dt(-14),
        )
        await doc_repo.create(alice_payments)

    # Priya's QA Test Strategy KT Document
    priya_qa = await doc_repo.get("doc_qa_regression_kt")
    if not priya_qa:
        priya_qa = Document(
            id="doc_qa_regression_kt",
            title="Automated Test Strategy & Quality Gates KT",
            content=(
                "Automated QA Regression Suite Architecture.\n\n"
                "Quality Gates:\n"
                "1. Unit Tests: Run on every PR with pytest.\n"
                "2. Contract Tests: Run via Pact to verify backend API schemas.\n"
                "3. End-to-End Regression: Automated suite verifies login, task workflow, and document indexing.\n"
                "Failure SLA: Test failures block staging deployments automatically."
            ),
            category="kt",
            tags=["qa", "testing", "regression", "ci_cd"],
            author_id="usr_priya",
            department_id="dept_engineering",
            is_public=False,
            scope=DocumentScope.PERSONAL,
            file_type="txt",
            file_size=820,
            status=ProcessingStatus.INDEXED,
            version=1,
            created_at=_dt(-10),
            updated_at=_dt(-10),
        )
        await doc_repo.create(priya_qa)

    # ── 4. Historical Incident Records ─────────────────────────────────────────
    inc1 = await inc_repo.get("inc_redis_eviction")
    if not inc1:
        inc1 = Incident(
            id="inc_redis_eviction",
            title="INC-402: Redis Session Cache Eviction Spike",
            description="Sudden surge in HTTP 401 errors caused by aggressive session cache key eviction in Redis cluster.",
            severity=IncidentSeverity.P2,
            status=IncidentStatus.RESOLVED,
            reporter_id="usr_alice",
            resolution_notes=(
                "Increased Redis memory limit to 8GB, switched eviction policy to volatile-lru, "
                "and enabled connection pool keepalive. No recurring 401 spikes observed."
            ),
            created_at=_dt(-45),
            resolved_at=_dt(-45, 2),
        )
        await inc_repo.create(inc1)

    inc2 = await inc_repo.get("inc_oauth_refresh")
    if not inc2:
        inc2 = Incident(
            id="inc_oauth_refresh",
            title="INC-508: OAuth Token Refresh Race Condition",
            description="Concurrent browser tabs attempting refresh token exchange simultaneously resulted in invalid token revocation.",
            severity=IncidentSeverity.P1,
            status=IncidentStatus.RESOLVED,
            reporter_id="usr_alice",
            resolution_notes=(
                "Implemented distributed lock in Redis keyed by user_id during token rotation exchange. "
                "Subsequent requests within 10-second grace window reuse current active token."
            ),
            created_at=_dt(-20),
            resolved_at=_dt(-20, 1),
        )
        await inc_repo.create(inc2)

    # ── 5. Seed Sample Brand Compliance Reports ────────────────────────────────
    report1 = await bcr_repo.get("bcr_sample_compliant")
    if not report1:
        await bcr_repo.create(
            BrandComplianceReport(
                id="bcr_sample_compliant",
                image_id="img_hero_banner",
                image_url=None,
                image_filename="hyperrealm_official_hero.png",
                guideline_id="guide_brand_identity",
                guideline_version="2.1",
                status=ComplianceStatus.COMPLIANT,
                summary="Hero banner satisfies all brand guidelines: approved #6366F1 indigo palette, 32px logo clearance, and Outfit typography.",
                checks=[
                    {
                        "requirement": "Color palette adherence to #6366F1 Hyper Indigo.",
                        "observed_evidence": "Primary color #6366F1 detected with 9.2:1 contrast.",
                        "result": "Passed",
                        "supporting_source": "Hyperrealm Brand Identity Standards v2.1 §2.1",
                    },
                    {
                        "requirement": "Logo clear space >= 24px buffer.",
                        "observed_evidence": "Verified 32px safe zone padding surrounding brand icon.",
                        "result": "Passed",
                        "supporting_source": "Hyperrealm Brand Identity Standards v2.1 §3.4",
                    },
                ],
                observed_evidence={"dimensions": "1920x1080", "logo_clearance_px": 32},
                guideline_reference="Hyperrealm Brand Identity & Design Standards v2.1",
                severity="none",
                recommendations=["Approved for public web presentation."],
                limitations=["Evaluation performed against digital RGB standard."],
                analysis_status="simulated_demo",
                created_by=admin_id,
                created_at=_dt(-5),
            )
        )

    print("[OK] Phase 04 seed data loaded successfully")
