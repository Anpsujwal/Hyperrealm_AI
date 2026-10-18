"""
HYPERREALM Collaborate Agent.
Specialist responsible for SME discovery, meeting coordination, calendar querying,
Scrum alignment, and action item extraction from meeting notes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..config import get_settings
from ..dependencies import get_dept_repo, get_meeting_repo, get_project_repo, get_proposal_repo, get_user_repo
from ..models import Meeting, MeetingProposal, MeetingType, UserProfile, UserRole, new_id, utcnow
from ..routes.meetings import _find_conflicts, _suggest_alternative_slots, _to_ist_full_str, IST
from ..services.calendar_service import get_calendar_service
from ..services.retrieval import EnterpriseRetrievalService
from ..services.workflow import WorkflowService

logger = logging.getLogger("hyperrealm.agents.collaborate")


class CollaborateAgent:
    name = "collaborate"
    description = (
        "Identifies subject-matter experts (SMEs) and managers, drafts follow-up messages, "
        "and coordinates meetings with pending proposals and explicit confirmation workflows."
    )

    def __init__(
        self,
        retrieval_service: Optional[EnterpriseRetrievalService] = None,
        workflow_service: Optional[WorkflowService] = None,
    ):
        self.retrieval = retrieval_service or EnterpriseRetrievalService()
        self.workflow = workflow_service or WorkflowService()

    @property
    def user_repo(self):
        return get_user_repo()

    @property
    def dept_repo(self):
        return get_dept_repo()

    @property
    def meeting_repo(self):
        return get_meeting_repo()

    @property
    def project_repo(self):
        return get_project_repo()

    @property
    def proposal_repo(self):
        return get_proposal_repo()

    async def execute(
        self,
        prompt: str,
        user: UserProfile,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Execute collaboration flow:
        1. Find SME, project lead, or actual manager matching requested topic.
        2. Draft message or formulate a pending meeting proposal for explicit confirmation.
        3. Never mark as scheduled or generate Meet links before explicit user confirmation.
        4. Clearly disclose simulation in demonstration mode.
        """
        settings = get_settings()
        prompt_lower = prompt.lower()

        # 1. Action item extraction from meeting notes
        if "action items" in prompt_lower or "blockers" in prompt_lower or "transcript" in prompt_lower:
            return await self._extract_action_items(prompt)

        # 2. Resolve target attendee (Distinguish manager from SME)
        target_user, target_role = await self._resolve_target_attendee(prompt, user, context)

        # If manager requested but cannot be identified reliably, prompt user for clarification
        if target_user is None and target_role == "manager_unresolved":
            return {
                "agent_id": self.name,
                "response": (
                    "I checked your employee profile and reporting hierarchy, but could not identify your direct reporting manager.\n\n"
                    "Whom would you like to schedule this meeting with? Please specify their name or email address."
                ),
                "proposed_actions": [],
                "citations": [],
                "is_simulated": settings.is_demo,
            }

        # Fallback if no target could be found at all
        if target_user is None:
            target_user = await self._find_sme(prompt, user)
            target_role = "Subject-Matter Expert"

        # Check if user wants to schedule a meeting
        if any(w in prompt_lower for w in ("schedule", "book", "calendar", "meet", "invite", "sync", "1:1", "connect")):
            # Determine proposed time in IST (tomorrow at 11:00 AM IST)
            sched_ist = (datetime.now(IST) + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
            sched_time = sched_ist.astimezone(timezone.utc).replace(tzinfo=None)

            # Context-aware meeting topic
            if context and context.get("onboard_topic"):
                meeting_title = f"1:1 Sync: {user.name} & {target_user.name} - Onboarding & Alignment"
            elif context and context.get("incident_topic"):
                meeting_title = f"Technical Review: {user.name} & {target_user.name} - {context.get('incident_topic')}"
            elif "manager" in prompt_lower or target_role == "Manager":
                meeting_title = f"1:1 Sync: {user.name} & {target_user.name} - Progress & Alignment"
            else:
                meeting_title = f"KT Sync: {user.name} & {target_user.name} on Technical Topics"

            # Check calendar availability & collisions
            participants = {user.id, target_user.id}
            conflicts = await _find_conflicts(
                meeting_repo=self.meeting_repo,
                user_repo=self.user_repo,
                scheduled_at=sched_time,
                duration_minutes=30,
                participant_ids=participants,
            )
            if conflicts:
                suggested_slots = await _suggest_alternative_slots(
                    meeting_repo=self.meeting_repo,
                    scheduled_at=sched_time,
                    duration_minutes=30,
                    participant_ids=participants,
                )
                if suggested_slots:
                    sched_time = suggested_slots[0]
                    sched_ist = sched_time.replace(tzinfo=timezone.utc).astimezone(IST)
                avail_note = f"⚠️ Adjusted to next available conflict-free slot: {_to_ist_full_str(sched_time)}."
            else:
                avail_note = "✅ Availability checked: Both participants are free with no calendar collisions."

            # Calendar integration status
            cal_svc = get_calendar_service()
            has_cal = bool(cal_svc.is_enabled and hasattr(user, "oauth_tokens") and user.oauth_tokens.get("google_calendar"))
            cal_status_text = (
                "Google Calendar Connected (Google Meet link will be requested upon confirmation)"
                if has_cal else
                "Local simulation mode (No external Google Calendar account linked)"
            )

            # Create pending proposal record (NO meeting or google event is created yet!)
            proposal = MeetingProposal(
                id=new_id("prop_"),
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                target_user_id=target_user.id,
                target_name=target_user.name,
                target_email=target_user.email,
                target_role=target_role,
                title=meeting_title,
                description=f"Meeting proposed via HYPERREALM Collaborate Agent regarding '{prompt}'.",
                scheduled_at=sched_time,
                duration_minutes=30,
                timezone="IST (UTC+05:30)",
                calendar_status=cal_status_text,
                availability_checked=True,
                availability_note=avail_note,
                status="pending_confirmation",
            )
            await self.proposal_repo.create(proposal)

            formatted_time_ist = _to_ist_full_str(sched_time)

            response = (
                f"**Collaboration & Meeting Coordination**\n\n"
                f"I identified **{target_user.name}** ({target_user.job_title}, {target_user.department_name or 'Engineering'}) "
                f"as your verified **{target_role}**.\n\n"
                f"### 📅 Proposed Meeting Details\n"
                f"- **Topic & Purpose:** {meeting_title}\n"
                f"- **Target Participant:** {target_user.name} ({target_user.email}) — *{target_role}*\n"
                f"- **Logged-in User:** {user.name} ({user.email})\n"
                f"- **Proposed Date & Time:** {formatted_time_ist}\n"
                f"- **Duration:** 30 minutes\n"
                f"- **Time Zone:** Indian Standard Time (IST, UTC+05:30)\n"
                f"- **Calendar / Meet Integration:** {cal_status_text}\n"
                f"- **Availability Status:** {avail_note}\n\n"
                f"> ℹ️ **Status:** Pending explicit user confirmation. No calendar event, Meet link, or invitations have been sent yet.\n"
                f"> Please review the proposal below and click **Confirm & Schedule** to schedule, or **Choose Another Time** to adjust."
            )

            action_params = {
                "action_type": "schedule_meeting_proposal",
                "title": f"Meeting with {target_user.name}: {meeting_title}",
                "description": f"Proposed meeting with {target_user.name} ({target_role}) on {formatted_time_ist}",
                "requires_approval": False,
                "proposal_id": proposal.id,
                "payload": {
                    "proposal_id": proposal.id,
                    "title": meeting_title,
                    "target_user_id": target_user.id,
                    "target_name": target_user.name,
                    "target_email": target_user.email,
                    "target_role": target_role,
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_email": user.email,
                    "scheduled_at": proposal.scheduled_at.isoformat(),
                    "scheduled_at_ist": formatted_time_ist,
                    "duration_minutes": 30,
                    "timezone": "IST (UTC+05:30)",
                    "calendar_status": cal_status_text,
                    "availability_checked": True,
                    "availability_note": avail_note,
                    "status": "pending_confirmation",
                },
            }

            return {
                "agent_id": self.name,
                "response": response,
                "proposed_actions": [action_params],
                "proposal_id": proposal.id,
                "citations": [{
                    "source_type": "user_directory",
                    "user_id": target_user.id,
                    "name": target_user.name,
                    "title": target_user.job_title,
                    "role": target_role,
                }],
                "is_simulated": settings.is_demo,
            }

        # Just expert recommendation & draft message
        draft_msg = (
            f"> \"Hi {target_user.name.split()[0]}, I am working through the materials on {prompt.strip()} and "
            f"had a couple of questions. Would you have 15 minutes for a quick sync this week?\""
        )
        is_sim = settings.is_demo

        if not settings.is_demo:
            try:
                from .adk_runtime import call_gemini_model
                sys_inst = (
                    f"You are the Hyperrealm Collaborate Specialist. Draft a concise, courteous message from {user.name} "
                    f"to {target_role} {target_user.name} ({target_user.job_title}) regarding '{prompt}'."
                )
                live_draft = await call_gemini_model(prompt=f"Draft outreach to {target_user.name} about: {prompt}", system_instruction=sys_inst)
                if live_draft:
                    draft_msg = f"> \"{live_draft.strip().strip('\"')}\""
                    is_sim = False
            except Exception as exc:
                logger.warning("Gemini outreach drafting failed (%s), using local template", exc)

        response = (
            f"**{target_role} Recommendation**\n\n"
            f"The designated contact for this topic is **{target_user.name}** ({target_user.job_title}).\n\n"
            f"**Relevant Skills & Projects:**\n"
            f"- Skills: {', '.join(target_user.skills)}\n"
            f"- Projects: {', '.join(target_user.project_ids)}\n\n"
            f"**Draft Message to {target_user.name.split()[0]}:**\n"
            f"{draft_msg}\n\n"
            f"Say *'Schedule a meeting with {target_user.name}'* if you would like me to propose a calendar invite."
        )

        return {
            "agent_id": self.name,
            "response": response,
            "citations": [{
                "source_type": "user_directory",
                "user_id": target_user.id,
                "name": target_user.name,
                "title": target_user.job_title,
                "role": target_role,
            }],
            "is_simulated": is_sim,
        }

    async def _resolve_target_attendee(
        self, prompt: str, user: UserProfile, context: Optional[dict[str, Any]] = None
    ) -> tuple[Optional[UserProfile], str]:
        """
        Resolve the target person for collaboration:
        - If prompt specifically asks for manager/lead/1:1, resolve from user.manager_id or org hierarchy.
        - If a specific name or email is mentioned, search user directory.
        - Otherwise, search for an SME.
        - Do NOT assume Ayesha Hussain is the manager simply because she is an SME.
        """
        p_lower = prompt.lower()
        is_manager_query = any(w in p_lower for w in ("manager", "reporting manager", "supervisor", "my lead", "1:1 with my manager", "sync with manager", "meet manager", "talk to my manager"))

        # 1. User specifically wants to meet with their manager
        if is_manager_query:
            if user.manager_id:
                manager = await self.user_repo.get(user.manager_id)
                if manager:
                    return manager, "Manager"

            # Check department head if user is not the head
            if user.department_id:
                dept = await self.dept_repo.get(user.department_id)
                if dept and dept.head_user_id and dept.head_user_id != user.id:
                    dept_head = await self.user_repo.get(dept.head_user_id)
                    if dept_head:
                        return dept_head, "Department Head / Manager"

            # Manager cannot be identified reliably from profile hierarchy
            return None, "manager_unresolved"

        # 2. Check if a specific colleague or name/email was mentioned
        users, _ = await self.user_repo.list(skip=0, limit=50)
        for u in users:
            if u.id != user.id:
                if u.email.lower() in p_lower or u.name.lower() in p_lower:
                    is_mgr = (user.manager_id == u.id)
                    return u, ("Manager" if is_mgr else (u.job_title or "Colleague"))
                # Match first name if at least 3 letters
                fname = u.name.split()[0].lower()
                if len(fname) >= 3 and f" {fname} " in f" {p_lower} ":
                    is_mgr = (user.manager_id == u.id)
                    return u, ("Manager" if is_mgr else (u.job_title or "Colleague"))

        # 3. Default to SME discovery (subject-matter expert)
        sme = await self._find_sme(prompt, user)
        return sme, "Subject-Matter Expert"

    async def _find_sme(self, prompt: str, user: UserProfile) -> UserProfile:
        """Find most suitable SME from user directory matching skills or role."""
        users, _ = await self.user_repo.list(skip=0, limit=50)
        p_lower = prompt.lower()

        # Prioritize QA Lead / Tech Lead for quality / tests
        if any(w in p_lower for w in ("test", "qa", "quality", "selenium", "gate")):
            for u in users:
                if u.id != user.id and ("QA" in u.job_title or any("test" in s.lower() for s in u.skills)):
                    return u

        # Security SME
        if any(w in p_lower for w in ("security", "auth", "jwt", "zero trust", "token")):
            for u in users:
                if u.id != user.id and (any("security" in s.lower() for s in u.skills) or u.role == UserRole.ADMIN):
                    return u

        # Other colleagues
        for u in users:
            if u.id != user.id and u.role in (UserRole.TECHNICAL_LEAD, UserRole.ADMIN, UserRole.SOFTWARE_DEVELOPER):
                return u

        # Default fallback to first non-self user or self
        for u in users:
            if u.id != user.id:
                return u
        return user

    async def _extract_action_items(self, notes: str) -> dict[str, Any]:
        """Extract structured decisions, blockers, and action items."""
        settings = get_settings()
        response = None
        is_sim = settings.is_demo

        if not settings.is_demo and notes:
            try:
                from .adk_runtime import call_gemini_model
                sys_inst = (
                    "You are the Hyperrealm Agile & Scrum Specialist. Analyze the provided meeting notes or transcript. "
                    "Extract structured Key Decisions, Action Items (with priority, owner, description), and Blockers/Risks."
                )
                live_extracted = await call_gemini_model(prompt=f"Meeting Notes:\n{notes}", system_instruction=sys_inst)
                if live_extracted:
                    response = live_extracted
                    is_sim = False
            except Exception as exc:
                logger.warning("Gemini action items extraction failed (%s), using local template", exc)

        if not response:
            response = (
                f"**Meeting Analysis & Action Items Extraction**\n\n"
                f"**Key Decisions:**\n"
                f"- Decided to adhere to standard OAuth 2.0 PKCE token refresh flow.\n"
                f"- Sprints will gate QA automated regression before deployment.\n\n"
                f"**Action Items Identified:**\n"
                f"1. [P1] Deploy Redis cache eviction monitoring (Assignee: DevOps).\n"
                f"2. [P2] Update payments KT documentation with sandbox webhooks (Assignee: Engineering Lead).\n\n"
                f"**Blockers / Risks:**\n"
                f"- Awaiting external third-party sandbox credentials."
            )

        return {
            "agent_id": self.name,
            "response": response,
            "citations": [],
            "proposed_actions": [],
            "is_simulated": is_sim,
        }
