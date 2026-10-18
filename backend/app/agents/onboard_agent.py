"""
HYPERREALM Onboard Agent.
Specialist responsible for personalized role-based onboarding plans,
learning resource recommendations, guideline explanations, and knowledge gap tracking.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import get_settings
from ..dependencies import get_guide_repo, get_learning_repo, get_project_repo
from ..models import (
    DocumentScope,
    Guideline,
    LearningResource,
    LearningStatus,
    OnboardingFormStatus,
    UserProfile,
    UserRole,
)
from ..services.onboarding_service import get_onboarding_service
from ..services.retrieval import EnterpriseRetrievalService
from .adk_runtime import call_gemini_model

logger = logging.getLogger("hyperrealm.agents.onboard")


class OnboardAgent:
    name = "onboard"
    description = (
        "Constructs role-specific onboarding paths, recommends mandatory learning, "
        "and coordinates complete associate onboarding journey."
    )

    def __init__(
        self,
        retrieval_service: Optional[EnterpriseRetrievalService] = None,
    ):
        self.retrieval = retrieval_service or EnterpriseRetrievalService()
        self.learning_repo = get_learning_repo()
        self.guide_repo = get_guide_repo()
        self.project_repo = get_project_repo()

    async def execute(
        self,
        prompt: str,
        user: UserProfile,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Orchestrate personalized onboarding assistance grounded in the user's
        actual onboarding journey and company policies.
        """
        service = get_onboarding_service()
        journey = await service.get_or_create_journey(user)

        role_label = user.role.value.replace("_", " ").title() if hasattr(user.role, "value") else str(user.role).title()
        dept_label = user.department_name or "Engineering"
        p_lower = prompt.lower()

        # 1. Fetch official guidelines for grounding
        guidelines, _ = await self.guide_repo.list(skip=0, limit=5, status="published")
        citations: list[dict[str, Any]] = []
        for g in guidelines[:2]:
            citations.append({
                "source_type": "official_guideline",
                "title": g.title,
                "version": g.version,
            })

        proposed_actions = []

        # ─── CASE A: "What do I need to complete this week?" ──────────────────
        if "week" in p_lower or "due soon" in p_lower or "timeline" in p_lower:
            pending_forms = [f for f in journey.forms if f.due_days <= 7 and f.status == OnboardingFormStatus.PENDING]
            active_courses = [c for c in journey.courses if c.is_mandatory and c.status != LearningStatus.COMPLETED][:3]
            unscheduled_intros = [i for i in journey.introductions if i.status == "unassigned"]

            form_bullets = "\n".join(f"- **{f.title}** (Due in {f.due_days} days) — Category: `{f.category.title()}`" for f in pending_forms) or "- All Week 1 compliance forms completed!"
            course_bullets = "\n".join(f"- **{c.title}** ({c.estimated_minutes} min) — Status: `{c.status.value}`" for c in active_courses) or "- All foundational courses for this week are completed!"
            intro_bullets = "\n".join(f"- **{i.person_name}** ({i.relationship}) — Purpose: {i.meeting_purpose}" for i in unscheduled_intros[:2]) or "- All key introductions are already scheduled!"

            response = (
                f"### Week 1 Onboarding Priorities for {user.name} ({role_label})\n\n"
                f"**Overall Progress:** {journey.completion_pct}% complete | **Next Action:** {journey.next_action}\n\n"
                f"#### Required Compliance Documents (Due This Week)\n{form_bullets}\n\n"
                f"#### Mandatory Learning Modules\n{course_bullets}\n\n"
                f"#### Recommended Introductions\n{intro_bullets}\n\n"
                f"Tip: You can submit your documents and schedule meetings directly from the **Onboarding Journey** tab in My Learning."
            )

        # ─── CASE B: "Which courses are waiting for manager approval?" ─────────
        elif "approval" in p_lower or "waiting" in p_lower or "pending courses" in p_lower:
            pending_courses = [c for c in journey.courses if c.approval_status == "pending_approval"]
            approved_electives = [c for c in journey.courses if c.approval_status == "approved" and not c.is_mandatory]
            manager_name = journey.manager_name or "your manager"

            if pending_courses:
                course_list = "\n".join(f"- **{c.title}** ({c.estimated_minutes} min) — *{c.reason}*" for c in pending_courses)
                response = (
                    f"### Courses Pending Manager Approval\n\n"
                    f"The following {len(pending_courses)} elective course(s) are currently submitted for approval by **{manager_name}**:\n\n"
                    f"{course_list}\n\n"
                    f"Once {manager_name} reviews and approves them, they will be automatically assigned to your **My Learning** curriculum."
                )
            else:
                approved_list = "\n".join(f"- **{c.title}** (Approved by manager)" for c in approved_electives) if approved_electives else ""
                response = (
                    f"### Course Approval Status\n\n"
                    f"You currently have **0 courses waiting for manager approval**.\n\n"
                    + (f"**Approved electives already in your learning hub:**\n{approved_list}\n\n" if approved_list else "")
                    + f"To request additional specialization courses, select electives in your **My Learning** page and click **Request Manager Approval**."
                )

        # ─── CASE C: "Who should I meet next?" ────────────────────────────────
        elif "meet" in p_lower or "who should i" in p_lower or "connect" in p_lower:
            unscheduled = [i for i in journey.introductions if i.status == "unassigned"]
            scheduled = [i for i in journey.introductions if i.status in ("scheduled", "completed")]

            if unscheduled:
                next_person = unscheduled[0]
                others = unscheduled[1:]
                other_text = "\n".join(f"- **{i.person_name}** ({i.relationship}): {i.meeting_purpose}" for i in others)

                response = (
                    f"### Recommended Next Introduction: **{next_person.person_name}**\n\n"
                    f"**Relationship:** `{next_person.relationship}` | **Role:** {next_person.role}\n"
                    f"**Suggested Agenda:** {next_person.meeting_purpose}\n\n"
                    + (f"#### Additional Upcoming Introductions:\n{other_text}\n\n" if other_text else "")
                    + f"You can schedule this 1:1 directly in the **Onboarding Journey** console or by saying *'Schedule intro with {next_person.person_name}'*."
                )
                proposed_actions.append({
                    "action_type": "schedule_onboarding_intro",
                    "title": f"Schedule 1:1 with {next_person.person_name} ({next_person.relationship})",
                    "description": f"Calendar invite for 30-min onboarding intro: {next_person.meeting_purpose}",
                    "intro_id": next_person.id,
                    "requires_approval": False,
                })
            else:
                response = (
                    f"### Introductions Complete\n\n"
                    f"All key onboarding introductions have been scheduled or completed with your manager, buddy, and team stakeholders!"
                )

        # ─── CASE D: "Which forms are pending?" ───────────────────────────────
        elif "form" in p_lower or "document" in p_lower or "i-9" in p_lower or "direct deposit" in p_lower:
            pending = [f for f in journey.forms if f.status == OnboardingFormStatus.PENDING]
            submitted = [f for f in journey.forms if f.status in (OnboardingFormStatus.SUBMITTED, OnboardingFormStatus.VERIFIED)]

            if pending:
                pending_lines = "\n".join(f"- **{f.title}** (Due: {f.due_date.strftime('%b %d, %Y') if f.due_date else 'Soon'}) — *{f.description}*" for f in pending)
                response = (
                    f"### Pending Onboarding Forms ({len(pending)} remaining)\n\n"
                    f"Please complete and submit the following required documents:\n\n"
                    f"{pending_lines}\n\n"
                    f"Note: Sensitive banking and identity numbers are strictly encrypted with least-privilege access and are never shared in public channels."
                )
            else:
                response = (
                    f"### All Onboarding Forms Completed!\n\n"
                    f"You have submitted all {len(submitted)} required onboarding forms and compliance agreements. HR has logged your submissions."
                )

        # ─── CASE E: Default Comprehensive Journey Summary ────────────────────
        else:
            completed_c = sum(1 for c in journey.courses if c.status == LearningStatus.COMPLETED)
            total_c = len(journey.courses)
            pending_forms_count = sum(1 for f in journey.forms if f.status == OnboardingFormStatus.PENDING)
            unscheduled_intros_count = sum(1 for i in journey.introductions if i.status == "unassigned")

            response = (
                f"**Personalized Onboarding & Learning Journey for {user.name}**\n\n"
                f"**Role:** `{role_label}` | **Department:** `{dept_label}` | **Manager:** `{journey.manager_name or 'Bob Harris'}` | **Buddy:** `{journey.buddy_name or 'Carol Adams'}`\n\n"
                f"**Overall Onboarding Progress: {journey.completion_pct}%**\n"
                f"- Learning Curriculum: {journey.learning_completion_pct}% ({completed_c}/{total_c} modules)\n"
                f"- Compliance Forms: {journey.forms_completion_pct}% ({pending_forms_count} pending)\n"
                f"- Team Introductions: {journey.intros_completion_pct}% ({unscheduled_intros_count} unscheduled)\n\n"
                f"### Next Priority Action\n"
                f"👉 **{journey.next_action}**\n\n"
                f"### Organizational Policies Grounding\n"
                + "\n".join(f"- **{g.title}** (v{g.version}): {g.description or 'Company-wide standard.'}" for g in guidelines[:2])
                + "\n\nTrack your live journey, request course approvals, and submit forms in the **My Learning** hub."
            )

        settings = get_settings()
        is_sim = settings.is_demo

        if not settings.is_demo:
            try:
                sys_inst = (
                    f"You are the Hyperrealm Onboarding Specialist serving new hire {user.name} ({role_label}). "
                    f"Structure your guidance clearly, encouraging progress on their next action: '{journey.next_action}'."
                )
                live_text = await call_gemini_model(prompt=f"User Query: {prompt}\n\nCurrent Journey Status:\n{response}", system_instruction=sys_inst)
                if live_text:
                    response = live_text
                    is_sim = False
            except Exception as exc:
                logger.warning("Gemini onboarding synthesis failed (%s), using local response", exc)

        return {
            "agent_id": self.name,
            "response": response,
            "citations": citations,
            "proposed_actions": proposed_actions,
            "is_simulated": is_sim,
            "learning_summary": {
                "role": role_label,
                "completion_pct": journey.completion_pct,
                "learning_completion_pct": journey.learning_completion_pct,
                "forms_completion_pct": journey.forms_completion_pct,
                "intros_completion_pct": journey.intros_completion_pct,
            },
        }
