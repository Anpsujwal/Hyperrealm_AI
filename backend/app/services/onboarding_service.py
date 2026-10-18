"""
HYPERREALM Onboarding Service.
Deterministic coordinator of personalized onboarding plans, manager approvals,
automatic learning assignments, introductions, compliance forms, and progress tracking.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..config import get_settings
from ..dependencies import (
    get_approval_repo,
    get_audit_repo,
    get_dept_repo,
    get_learning_repo,
    get_meeting_repo,
    get_notif_repo,
    get_onboarding_repo,
    get_project_repo,
    get_user_repo,
)
from ..models import (
    Approval,
    ApprovalStatus,
    AuditAction,
    AuditRecord,
    LearningResource,
    LearningStatus,
    Meeting,
    MeetingType,
    Notification,
    NotificationType,
    OnboardingCourseItem,
    OnboardingFormRequirement,
    OnboardingFormStatus,
    OnboardingIntroduction,
    OnboardingJourney,
    OnboardingStepStatus,
    UserLearningProgress,
    UserProfile,
    UserRole,
    new_id,
    utcnow,
)

logger = logging.getLogger("hyperrealm.services.onboarding")


def _to_naive_utc(dt: Any) -> Optional[datetime]:
    """Normalize datetime or ISO string to naive UTC datetime for safe comparisons."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return None
    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    return None


def _is_past(dt: Any) -> bool:
    """Safe comparison against current naive UTC."""
    target = _to_naive_utc(dt)
    if not target:
        return False
    return target < datetime.utcnow()


class OnboardingService:
    def __init__(self):
        self.onb_repo = get_onboarding_repo()
        self.user_repo = get_user_repo()
        self.dept_repo = get_dept_repo()
        self.learning_repo = get_learning_repo()
        self.approval_repo = get_approval_repo()
        self.meeting_repo = get_meeting_repo()
        self.notif_repo = get_notif_repo()
        self.audit_repo = get_audit_repo()
        self.project_repo = get_project_repo()

    async def get_or_create_journey(self, user: UserProfile, force_refresh: bool = False) -> OnboardingJourney:
        """
        Retrieve existing persistent onboarding journey or generate a new personalized plan
        grounded in the organization hierarchy, catalog, and configured policies.
        """
        existing = await self.onb_repo.get_by_user(user.id)
        if existing and not force_refresh:
            return await self.sync_journey_progress(existing)

        journey = await self._generate_personalized_journey(user)
        if existing:
            journey.id = existing.id
            saved = await self.onb_repo.update(journey)
        else:
            saved = await self.onb_repo.create(journey)

        return await self.sync_journey_progress(saved)

    async def _generate_personalized_journey(self, user: UserProfile) -> OnboardingJourney:
        """Construct deterministic, personalized onboarding journey."""
        role_label = user.role.value if hasattr(user.role, "value") else str(user.role)
        dept_name = user.department_name or "Engineering"

        # 1. Manager & Buddy identification from Org hierarchy
        manager: Optional[UserProfile] = None
        if user.manager_id:
            manager = await self.user_repo.get(user.manager_id)

        # Peer buddy: find colleague with same department/project, not self, not manager
        all_users, _ = await self.user_repo.list(limit=50)
        peers = [
            u for u in all_users
            if u.id != user.id
            and u.id != user.manager_id
            and (u.department_id == user.department_id or u.role == user.role)
        ]
        buddy = peers[0] if peers else (manager or user)

        # 2. Courses from catalog
        resources, _ = await self.learning_repo.list_resources(limit=100)
        user_progress_list = await self.learning_repo.list_progress_by_user(user.id)
        prog_map = {p.resource_id: p for p in user_progress_list}

        course_items: list[OnboardingCourseItem] = []
        seq = 1

        # A. Mandatory courses (required for 'employee' or user's specific role)
        for r in resources:
            role_strs = [r_role.value if hasattr(r_role, "value") else str(r_role) for r_role in r.required_for_roles]
            is_mandatory = "employee" in role_strs or role_label in role_strs
            p = prog_map.get(r.id)

            if is_mandatory:
                course_items.append(
                    OnboardingCourseItem(
                        resource_id=r.id,
                        title=r.title,
                        description=r.description,
                        category=r.category,
                        estimated_minutes=r.estimated_minutes,
                        is_mandatory=True,
                        requires_approval=False,
                        approval_status="not_required",
                        sequence_order=seq,
                        status=p.status if p else LearningStatus.NOT_STARTED,
                        progress_pct=p.progress_pct if p else 0,
                        reason=f"Mandatory foundational compliance for {role_label.replace('_', ' ').title()}.",
                    )
                )
                seq += 1

        # B. Role-specific recommended electives (require manager approval)
        for r in resources:
            role_strs = [r_role.value if hasattr(r_role, "value") else str(r_role) for r_role in r.required_for_roles]
            is_mandatory = "employee" in role_strs or role_label in role_strs
            p = prog_map.get(r.id)

            if not is_mandatory:
                # Recommend complementary electives based on department / role
                is_relevant = False
                reason = "Recommended elective for career growth and cross-functional standards."
                if user.role in (UserRole.SOFTWARE_DEVELOPER, UserRole.TECHNICAL_LEAD) and r.category in ("engineering", "security"):
                    is_relevant = True
                    reason = "Deepens systems architecture and engineering quality standards."
                elif user.role == UserRole.QA_ENGINEER and r.category in ("engineering", "process"):
                    is_relevant = True
                    reason = "Reinforces test automation and defect prevention frameworks."
                elif user.role == UserRole.DEVOPS_ENGINEER and r.category in ("devops", "security"):
                    is_relevant = True
                    reason = "Critical for production infrastructure reliability and cloud governance."
                elif user.role == UserRole.PROJECT_MANAGER and r.category == "process":
                    is_relevant = True
                    reason = "Standardizes agile delivery and team scrum ceremonies."

                if is_relevant:
                    course_items.append(
                        OnboardingCourseItem(
                            resource_id=r.id,
                            title=r.title,
                            description=r.description,
                            category=r.category,
                            estimated_minutes=r.estimated_minutes,
                            is_mandatory=False,
                            requires_approval=True,
                            approval_status="approved" if p else "not_required",
                            sequence_order=seq,
                            status=p.status if p else LearningStatus.NOT_STARTED,
                            progress_pct=p.progress_pct if p else 0,
                            reason=reason,
                        )
                    )
                    seq += 1

        # 3. People to meet (Organization Chart grounded)
        introductions: list[OnboardingIntroduction] = []
        if manager:
            introductions.append(
                OnboardingIntroduction(
                    id=new_id("intro_"),
                    person_id=manager.id,
                    person_name=manager.name,
                    role=manager.job_title or (manager.role.value if hasattr(manager.role, "value") else str(manager.role)),
                    email=manager.email,
                    avatar_url=manager.avatar_url,
                    relationship="Reporting Manager",
                    meeting_purpose="Expectations alignment, 30-day goals, squad priority review, and bi-weekly 1:1 cadence.",
                    status="unassigned",
                )
            )

        if buddy and (not manager or buddy.id != manager.id):
            introductions.append(
                OnboardingIntroduction(
                    id=new_id("intro_"),
                    person_id=buddy.id,
                    person_name=buddy.name,
                    role=buddy.job_title or "Senior Peer",
                    email=buddy.email,
                    avatar_url=buddy.avatar_url,
                    relationship="Onboarding Buddy",
                    meeting_purpose="Dev setup walkthrough, PR review practices, codebase architecture tour, and unblocking questions.",
                    status="unassigned",
                )
            )

        # Department Head or Senior Stakeholder
        stakeholder_email = "alice.chen@hyperrealm.io" if dept_name == "Engineering" else "henry.park@hyperrealm.io"
        dept_head = await self.user_repo.get_by_email(stakeholder_email)
        if dept_head and dept_head.id != user.id and dept_head.id != (manager.id if manager else None):
            introductions.append(
                OnboardingIntroduction(
                    id=new_id("intro_"),
                    person_id=dept_head.id,
                    person_name=dept_head.name,
                    role=dept_head.job_title or "Department Leader",
                    email=dept_head.email,
                    avatar_url=dept_head.avatar_url,
                    relationship="Department Stakeholder",
                    meeting_purpose="Department mission overview, cross-functional roadmap review, and team charter alignment.",
                    status="unassigned",
                )
            )

        # 4. Mandatory Onboarding Forms & Documents
        now = utcnow()
        forms = [
            OnboardingFormRequirement(
                id="form_i9_identity",
                title="I-9 Employment Eligibility & Identity Verification",
                description="Federal identity and employment authorization documentation verification.",
                category="legal",
                is_sensitive=True,
                status=OnboardingFormStatus.PENDING,
                due_days=3,
                due_date=now + timedelta(days=3),
                prepopulated_fields={"name": user.name, "email": user.email, "role": role_label},
            ),
            OnboardingFormRequirement(
                id="form_direct_deposit",
                title="Direct Deposit & Payroll Banking Information",
                description="Secure bank account details setup for payroll disbursement and tax withholding.",
                category="payroll",
                is_sensitive=True,
                status=OnboardingFormStatus.PENDING,
                due_days=5,
                due_date=now + timedelta(days=5),
                prepopulated_fields={"employee_name": user.name, "email": user.email},
            ),
            OnboardingFormRequirement(
                id="form_code_of_conduct",
                title="Code of Conduct & Professional Ethics Agreement",
                description="Acknowledgement of workplace standards, anti-harassment policy, and conflict-of-interest guidelines.",
                category="compliance",
                is_sensitive=False,
                status=OnboardingFormStatus.PENDING,
                due_days=7,
                due_date=now + timedelta(days=7),
                prepopulated_fields={"employee_name": user.name, "department": dept_name},
            ),
            OnboardingFormRequirement(
                id="form_nda_ip",
                title="Non-Disclosure & Intellectual Property Assignment Agreement",
                description="Proprietary information protection, trade secrets compliance, and copyright assignments.",
                category="legal",
                is_sensitive=False,
                status=OnboardingFormStatus.PENDING,
                due_days=7,
                due_date=now + timedelta(days=7),
                prepopulated_fields={"employee_name": user.name, "date": now.strftime("%Y-%m-%d")},
            ),
            OnboardingFormRequirement(
                id="form_security_compliance",
                title="Information Security Policy & Device Compliance Sign-off",
                description="Encryption requirements, multi-factor authentication, acceptable use, and incident reporting acknowledgement.",
                category="security",
                is_sensitive=False,
                status=OnboardingFormStatus.PENDING,
                due_days=10,
                due_date=now + timedelta(days=10),
                prepopulated_fields={"employee_name": user.name, "email": user.email},
            ),
        ]

        # 5. Onboarding Steps / Milestones (Guaranteed normalized list)
        steps = [
            {
                "id": "step_day_1",
                "phase": "Day 1",
                "title": "Welcome & Foundations",
                "due_days": 1,
                "status": "in_progress",
                "items": [
                    "Complete I-9 Employment Eligibility form",
                    "Configure Direct Deposit banking setup",
                    "Meet with Reporting Manager for initial onboarding welcome",
                ],
            },
            {
                "id": "step_week_1",
                "phase": "Week 1",
                "title": "Compliance & Team Immersion",
                "due_days": 7,
                "status": "pending",
                "items": [
                    "Sign Code of Conduct & NDA agreements",
                    "Complete Mandatory Security Fundamentals course",
                    "Sync with Onboarding Buddy for architecture walkthrough",
                ],
            },
            {
                "id": "step_month_1",
                "phase": "Month 1",
                "title": "Role Specialization & Delivery",
                "due_days": 30,
                "status": "pending",
                "items": [
                    "Complete role-specific learning paths",
                    "Deliver first sprint PR or QA validation gate",
                    "Complete 30-day onboarding review with Manager",
                ],
            },
        ]

        journey = OnboardingJourney(
            id=new_id("onb_"),
            user_id=user.id,
            user_name=user.name,
            role=role_label,
            department=dept_name,
            manager_id=manager.id if manager else None,
            manager_name=manager.name if manager else None,
            buddy_id=buddy.id if buddy else None,
            buddy_name=buddy.name if buddy else None,
            start_date=user.created_at,
            completion_pct=0,
            learning_completion_pct=0,
            forms_completion_pct=0,
            intros_completion_pct=0,
            status="in_progress",
            courses=course_items,
            introductions=introductions,
            forms=forms,
            onboarding_steps=steps,
            blockers=[],
            next_action="Complete Day 1 compliance forms and schedule introductory 1:1 with your manager.",
            created_at=now,
            updated_at=now,
        )

        return journey

    async def sync_journey_progress(self, journey: OnboardingJourney) -> OnboardingJourney:
        """
        Deterministically recalculates progress percentages across learning,
        forms, and introductions, updating milestones and blocker notices.
        """
        # 0. Backfill user_name if missing
        if not getattr(journey, "user_name", None):
            u = await self.user_repo.get(journey.user_id)
            if u:
                journey.user_name = u.name

        # 1. Sync learning progress from real learning_repo
        user_progress_list = await self.learning_repo.list_progress_by_user(journey.user_id)
        prog_map = {p.resource_id: p for p in user_progress_list}

        total_courses = len(journey.courses)
        completed_courses = 0
        for c in journey.courses:
            p = prog_map.get(c.resource_id)
            if p:
                c.status = p.status
                c.progress_pct = p.progress_pct
                if p.status == LearningStatus.COMPLETED:
                    completed_courses += 1
            elif c.status == LearningStatus.COMPLETED:
                completed_courses += 1

        learning_pct = int((completed_courses / total_courses * 100)) if total_courses > 0 else 100

        # 2. Sync introductions from real meeting_repo
        scheduled_or_done = 0
        for intro in journey.introductions:
            if intro.meeting_id:
                m = await self.meeting_repo.get(intro.meeting_id)
                if m:
                    if _is_past(m.scheduled_at):
                        intro.status = "completed"
                        scheduled_or_done += 1
                    else:
                        intro.status = "scheduled"
                        scheduled_or_done += 1
            elif intro.status in ("scheduled", "completed"):
                scheduled_or_done += 1

        total_intros = len(journey.introductions)
        intros_pct = int((scheduled_or_done / total_intros * 100)) if total_intros > 0 else 100

        # 3. Forms progress
        total_forms = len(journey.forms)
        completed_forms = sum(1 for f in journey.forms if f.status in (OnboardingFormStatus.SUBMITTED, OnboardingFormStatus.VERIFIED))
        forms_pct = int((completed_forms / total_forms * 100)) if total_forms > 0 else 100

        # Weighted overall completion: Learning (40%), Forms (35%), Intros (25%)
        overall_pct = int((learning_pct * 0.4) + (forms_pct * 0.35) + (intros_pct * 0.25))

        # Check for blockers
        blockers = []
        now = utcnow()
        for f in journey.forms:
            if f.due_date and _is_past(f.due_date) and f.status == OnboardingFormStatus.PENDING:
                due_str = f.due_date.strftime('%Y-%m-%d') if hasattr(f.due_date, 'strftime') else str(f.due_date)[:10]
                blockers.append(f"Form '{f.title}' is overdue (due {due_str}).")

        pending_approvals = sum(1 for c in journey.courses if c.approval_status == "pending_approval")
        if pending_approvals > 0:
            blockers.append(f"{pending_approvals} recommended courses awaiting manager review.")

        # Determine next appropriate action
        next_action = "All onboarding milestones up to date! Proceed with team sprint tasks."
        if forms_pct < 100:
            pending_form = next((f for f in journey.forms if f.status == OnboardingFormStatus.PENDING), None)
            if pending_form:
                next_action = f"Complete required document: {pending_form.title}."
        elif intros_pct < 100:
            pending_intro = next((i for i in journey.introductions if i.status == "unassigned"), None)
            if pending_intro:
                next_action = f"Schedule introductory meeting with {pending_intro.person_name} ({pending_intro.relationship})."
        elif learning_pct < 100:
            next_course = next((c for c in journey.courses if c.status != LearningStatus.COMPLETED), None)
            if next_course:
                next_action = f"Continue learning track: {next_course.title}."

        journey.completion_pct = overall_pct
        journey.learning_completion_pct = learning_pct
        journey.forms_completion_pct = forms_pct
        journey.intros_completion_pct = intros_pct
        journey.blockers = blockers
        journey.next_action = next_action
        journey.updated_at = now

        # Update journey in storage
        await self.onb_repo.update(journey)
        return journey

    # ──────────────────────────────────────────────────────────────────────────
    # Phase 2: Manager Approval Workflow & Automatic Course Assignment
    # ──────────────────────────────────────────────────────────────────────────

    async def request_course_approval(
        self,
        user: UserProfile,
        course_ids: list[str],
        justification: str,
    ) -> tuple[Approval, OnboardingJourney]:
        """
        Creates a real Approval record and in-app Notification for the associate's manager.
        Flags the requested courses in the onboarding journey as pending approval.
        """
        settings = get_settings()
        journey = await self.get_or_create_journey(user)

        # Identify manager approver
        approver_id = user.manager_id
        if not approver_id:
            admin_user = await self.user_repo.get_by_email("bob.harris@hyperrealm.io")
            approver_id = admin_user.id if admin_user else user.id

        # Verify courses exist in catalog
        requested_courses: list[dict[str, Any]] = []
        for cid in course_ids:
            res = await self.learning_repo.get_resource(cid)
            if res:
                requested_courses.append({
                    "id": res.id,
                    "title": res.title,
                    "category": res.category,
                    "estimated_minutes": res.estimated_minutes,
                })

        # Update course items in journey
        for c in journey.courses:
            if c.resource_id in course_ids:
                c.requires_approval = True
                c.approval_status = "pending_approval"

        approval_title = f"Learning Plan Approval: {user.name} ({len(requested_courses)} courses)"
        approval_desc = (
            f"Associate {user.name} ({user.email}) has proposed {len(requested_courses)} courses "
            f"for their {user.role.value if hasattr(user.role, 'value') else str(user.role)} specialization track.\n"
            f"Business justification: {justification}"
        )

        approval = Approval(
            id=new_id("appr_"),
            title=approval_title,
            description=approval_desc,
            requester_id=user.id,
            approver_id=approver_id,
            status=ApprovalStatus.PENDING,
            action_type="course_assignment_approval",
            action_payload={
                "associate_id": user.id,
                "associate_name": user.name,
                "course_ids": course_ids,
                "courses": requested_courses,
                "justification": justification,
                "is_simulated": settings.is_demo,
            },
            evidence=f"Proposed on {utcnow().strftime('%Y-%m-%d %H:%M:%S')} via Onboard Agent.",
            risks=[],
            target_resource="learning_path",
            requested_at=utcnow(),
        )

        created_approval = await self.approval_repo.create(approval)

        # Store approval_id on journey course items
        for c in journey.courses:
            if c.resource_id in course_ids:
                c.approval_id = created_approval.id

        await self.onb_repo.update(journey)

        # In-app notification to manager
        await self.notif_repo.create(
            Notification(
                id=new_id("notif_"),
                user_id=approver_id,
                type=NotificationType.APPROVAL_REQUESTED,
                title="Learning Plan Approval Requested",
                body=f"{user.name} submitted {len(requested_courses)} courses for onboarding approval.",
                link="/app/learning",
            )
        )

        # Audit record
        await self.audit_repo.create(
            AuditRecord(
                actor_id=user.id,
                actor_email=user.email,
                action=AuditAction.CREATE,
                resource_type="approval",
                resource_id=created_approval.id,
                description=f"Requested course approval for {len(requested_courses)} courses.",
            )
        )

        return created_approval, journey

    async def resolve_course_approval(
        self,
        approval_id: str,
        approver: UserProfile,
        status: str,  # "approved" | "rejected"
        decision_note: str = "",
        approved_course_ids: Optional[list[str]] = None,
    ) -> tuple[Approval, Optional[OnboardingJourney]]:
        """
        Manager approves, modifies, or rejects recommended courses.
        On approval: automatically enrolls associate into courses, creates UserLearningProgress,
        updates the onboarding journey, and notifies associate.
        """
        approval = await self.approval_repo.get(approval_id)
        if not approval:
            raise ValueError("Approval request not found.")

        # RBAC Check: Approver must be designated approver or Admin
        is_admin = approver.role == UserRole.ADMIN
        if approval.approver_id != approver.id and not is_admin:
            raise PermissionError("Access denied: You are not authorized to resolve this approval request.")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request has already been resolved with status: {approval.status.value}.")

        associate_id = approval.requester_id
        associate = await self.user_repo.get(associate_id)
        if not associate:
            raise ValueError("Associate not found.")

        final_status = ApprovalStatus.APPROVED if status.lower() == "approved" else ApprovalStatus.REJECTED
        approval.status = final_status
        approval.decision_note = decision_note
        approval.resolved_at = utcnow()

        payload = approval.action_payload or {}
        requested_ids = payload.get("course_ids", [])
        final_course_ids = approved_course_ids if approved_course_ids is not None else requested_ids

        # Update approval in repo
        updated_approval = await self.approval_repo.update(approval)

        journey = await self.onb_repo.get_by_user(associate_id)

        if final_status == ApprovalStatus.APPROVED:
            # AUTOMATIC COURSE ASSIGNMENT
            for cid in final_course_ids:
                # Check if already exists in UserLearningProgress
                existing_prog = await self.learning_repo.get_progress(associate_id, cid)
                if not existing_prog:
                    new_prog = UserLearningProgress(
                        id=new_id("ulp_"),
                        user_id=associate_id,
                        resource_id=cid,
                        status=LearningStatus.NOT_STARTED,
                        progress_pct=0,
                        due_date=utcnow() + timedelta(days=30),
                        started_at=None,
                        completed_at=None,
                    )
                    await self.learning_repo.upsert_progress(new_prog)

            # Update journey state
            if journey:
                for c in journey.courses:
                    if c.resource_id in final_course_ids:
                        c.approval_status = "approved"
                    elif c.resource_id in requested_ids:
                        c.approval_status = "rejected"
                await self.onb_repo.update(journey)

            # In-app notification to associate
            await self.notif_repo.create(
                Notification(
                    id=new_id("notif_"),
                    user_id=associate_id,
                    type=NotificationType.APPROVAL_RESOLVED,
                    title="Learning Plan Approved!",
                    body=f"Manager {approver.name} approved {len(final_course_ids)} courses. They are now assigned to your My Learning curriculum.",
                    link="/app/learning",
                )
            )

        else:
            # REJECTED
            if journey:
                for c in journey.courses:
                    if c.resource_id in requested_ids:
                        c.approval_status = "rejected"
                await self.onb_repo.update(journey)

            # In-app notification to associate
            await self.notif_repo.create(
                Notification(
                    id=new_id("notif_"),
                    user_id=associate_id,
                    type=NotificationType.APPROVAL_RESOLVED,
                    title="Learning Plan Update",
                    body=f"Your manager {approver.name} reviewed your proposed courses. Note: {decision_note or 'No notes provided.'}",
                    link="/app/learning",
                )
            )

        # Audit record
        await self.audit_repo.create(
            AuditRecord(
                actor_id=approver.id,
                actor_email=approver.email,
                action=AuditAction.UPDATE,
                resource_type="approval",
                resource_id=approval.id,
                description=f"Resolved course approval as {final_status.value} for {associate.name}. Courses: {final_course_ids}",
            )
        )

        synced_journey = await self.sync_journey_progress(journey) if journey else None
        return updated_approval, synced_journey

    # ──────────────────────────────────────────────────────────────────────────
    # Phase 3: Introductions & Compliance Form Automation
    # ──────────────────────────────────────────────────────────────────────────

    async def schedule_introduction(
        self,
        user: UserProfile,
        intro_id: str,
        scheduled_at: Optional[datetime] = None,
        duration_minutes: int = 30,
        notes: str = "",
    ) -> tuple[Meeting, OnboardingJourney]:
        """
        Creates a real calendar Meeting in meeting_repo and links it to the onboarding intro.
        """
        settings = get_settings()
        journey = await self.get_or_create_journey(user)

        target_intro = next((i for i in journey.introductions if i.id == intro_id), None)
        if not target_intro:
            raise ValueError(f"Introduction with ID '{intro_id}' not found in onboarding plan.")

        target_person = await self.user_repo.get(target_intro.person_id)
        if not target_person:
            raise ValueError(f"Person '{target_intro.person_id}' not found.")

        sched_time = _to_naive_utc(scheduled_at) or (utcnow() + timedelta(days=2, hours=4))

        meeting = Meeting(
            id=new_id("meet_"),
            title=f"Onboarding 1:1: {user.name} & {target_person.name} ({target_intro.relationship})",
            type=MeetingType.ONE_ON_ONE,
            description=f"Purpose: {target_intro.meeting_purpose}\nNotes: {notes}",
            organiser_id=user.id,
            attendee_ids=[user.id, target_person.id],
            scheduled_at=sched_time,
            duration_minutes=duration_minutes,
            location="Virtual - Google Meet (Local Simulation)" if settings.is_demo else "https://meet.google.com/hpr-intro",
            agenda=[
                f"Welcome & role introduction: {user.name}",
                f"{target_intro.relationship} guidance & team responsibilities",
                "Q&A and open questions",
            ],
            notes=notes,
        )

        created_meeting = await self.meeting_repo.create(meeting)

        target_intro.meeting_id = created_meeting.id
        target_intro.status = "scheduled"
        await self.onb_repo.update(journey)

        # Notify attendee
        await self.notif_repo.create(
            Notification(
                id=new_id("notif_"),
                user_id=target_person.id,
                type=NotificationType.SYSTEM,
                title="New Onboarding 1:1 Scheduled",
                body=f"{user.name} scheduled an onboarding introduction with you for {sched_time.strftime('%Y-%m-%d %H:%M')}.",
                link="/app/meetings",
            )
        )

        # Audit record
        await self.audit_repo.create(
            AuditRecord(
                actor_id=user.id,
                actor_email=user.email,
                action=AuditAction.CREATE,
                resource_type="meeting",
                resource_id=created_meeting.id,
                description=f"Scheduled onboarding introduction with {target_person.name}",
            )
        )

        updated_journey = await self.sync_journey_progress(journey)
        return created_meeting, updated_journey

    async def submit_form(
        self,
        user: UserProfile,
        form_id: str,
        form_data: dict[str, Any],
        signature_confirmation: bool = True,
    ) -> OnboardingJourney:
        """
        Validates, securely records, and advances form requirement.
        Enforces field validation and sensitive data handling.
        """
        journey = await self.get_or_create_journey(user)

        target_form = next((f for f in journey.forms if f.id == form_id), None)
        if not target_form:
            raise ValueError(f"Form '{form_id}' not found in required onboarding documents.")

        # Deterministic form validation
        if form_id == "form_i9_identity":
            if not form_data.get("document_type") or not form_data.get("document_number"):
                raise ValueError("Validation error: Document Type and Document Number are required for I-9 verification.")
        elif form_id == "form_direct_deposit":
            if not form_data.get("bank_name") or not form_data.get("routing_number") or not form_data.get("account_number"):
                raise ValueError("Validation error: Bank Name, Routing Number, and Account Number are required for Direct Deposit.")
        elif form_id == "form_code_of_conduct":
            if not signature_confirmation:
                raise ValueError("Validation error: You must check the signature confirmation to agree to the Code of Conduct.")

        target_form.submitted_data = form_data
        target_form.status = OnboardingFormStatus.SUBMITTED
        target_form.submitted_at = utcnow()

        # Audit trail (without exposing sensitive values)
        sanitized_keys = list(form_data.keys())
        await self.audit_repo.create(
            AuditRecord(
                actor_id=user.id,
                actor_email=user.email,
                action=AuditAction.CREATE,
                resource_type="onboarding_form",
                resource_id=form_id,
                description=f"Submitted onboarding form: {target_form.title}",
                metadata={"form_id": form_id, "submitted_fields": sanitized_keys},
            )
        )

        await self.onb_repo.update(journey)
        return await self.sync_journey_progress(journey)


_onboarding_service: Optional[OnboardingService] = None


def get_onboarding_service() -> OnboardingService:
    global _onboarding_service
    if _onboarding_service is None:
        _onboarding_service = OnboardingService()
    return _onboarding_service
