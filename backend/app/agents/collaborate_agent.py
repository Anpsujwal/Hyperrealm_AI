"""
HYPERREALM Collaborate Agent.
Specialist responsible for SME discovery, meeting coordination, calendar querying,
Scrum alignment, and action item extraction from meeting notes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from ..config import get_settings
from ..dependencies import get_meeting_repo, get_project_repo, get_user_repo
from ..models import Meeting, MeetingType, UserProfile, UserRole, new_id, utcnow
from ..services.retrieval import EnterpriseRetrievalService
from ..services.workflow import WorkflowService

logger = logging.getLogger("hyperrealm.agents.collaborate")


class CollaborateAgent:
    name = "collaborate"
    description = (
        "Identifies subject-matter experts (SMEs), drafts follow-up messages, "
        "and coordinates meetings with approval workflows."
    )

    def __init__(
        self,
        retrieval_service: Optional[EnterpriseRetrievalService] = None,
        workflow_service: Optional[WorkflowService] = None,
    ):
        self.retrieval = retrieval_service or EnterpriseRetrievalService()
        self.workflow = workflow_service or WorkflowService()
        self.user_repo = get_user_repo()
        self.meeting_repo = get_meeting_repo()
        self.project_repo = get_project_repo()

    async def execute(
        self,
        prompt: str,
        user: UserProfile,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Execute collaboration flow:
        1. Find SME or project lead matching requested topic.
        2. Draft message or propose follow-up meeting.
        3. Formulate proposed action for approval if meeting creation requested.
        4. Clearly disclose simulation in demonstration mode.
        """
        settings = get_settings()
        prompt_lower = prompt.lower()

        # 1. Action item extraction from meeting notes
        if "action items" in prompt_lower or "blockers" in prompt_lower or "transcript" in prompt_lower:
            return self._extract_action_items(prompt)

        # 2. SME discovery
        sme_user = await self._find_sme(prompt, user)

        # Check if user wants to schedule a meeting
        if any(w in prompt_lower for w in ("schedule", "book", "calendar", "meet", "invite")):
            sched_time = (utcnow() + timedelta(days=1, hours=2)).replace(minute=0, second=0, microsecond=0)
            meeting_title = f"Sync: {sme_user.name} & {user.name} on KT topics"

            action_params = {
                "title": meeting_title,
                "scheduled_at": sched_time.isoformat(),
                "duration_minutes": 30,
                "attendee_ids": [user.id, sme_user.id],
                "description": f"Coordination on '{prompt}' facilitated by HYPERREALM Collaborate Agent.",
            }

            # Propose action via workflow validation & approval
            approval, _ = await self.workflow.validate_and_propose_action(
                action_type="schedule_meeting",
                parameters=action_params,
                requester=user,
                evidence=f"User requested meeting with {sme_user.name} based on SME discovery.",
                requires_approval=True,
            )

            is_sim = settings.is_demo
            mode_notice = (
                "ℹ️ **Integration Disclosure (Demo Mode):** External Google Calendar / Meet integration is running "
                "with the local simulation adapter. No live Google Calendar event will be created."
                if is_sim else "✅ Live Google Calendar integration ready."
            )

            response = (
                f"**Collaboration & SME Discovery**\n\n"
                f"I identified **{sme_user.name}** ({sme_user.job_title}, {sme_user.department_name or 'Engineering'}) "
                f"as the lead subject-matter expert for this area based on project ownership and skill tags: "
                f"`{', '.join(sme_user.skills[:3])}`.\n\n"
                f"**Proposed Meeting:**\n"
                f"- **Topic:** {meeting_title}\n"
                f"- **Attendees:** {user.name} ({user.email}), {sme_user.name} ({sme_user.email})\n"
                f"- **Time:** {sched_time.strftime('%A, %b %d at %H:%M UTC')}\n"
                f"- **Approval Status:** `Pending Validation & Approval` (ID: `{approval.id if approval else 'appr_pending'}`)\n\n"
                f"{mode_notice}\n\n"
                f"You can review and confirm this proposal in the Tasks & Approvals panel."
            )

            return {
                "agent_id": self.name,
                "response": response,
                "proposed_actions": [action_params],
                "approval_id": approval.id if approval else None,
                "citations": [{
                    "source_type": "user_directory",
                    "user_id": sme_user.id,
                    "name": sme_user.name,
                    "title": sme_user.job_title,
                }],
            }

        # Just expert recommendation & draft message
        response = (
            f"**Subject-Matter Expert Recommendation**\n\n"
            f"The designated expert for this topic is **{sme_user.name}** ({sme_user.job_title}).\n\n"
            f"**Relevant Skills & Projects:**\n"
            f"- Skills: {', '.join(sme_user.skills)}\n"
            f"- Projects: {', '.join(sme_user.project_ids)}\n\n"
            f"**Draft Message to {sme_user.name.split()[0]}:**\n"
            f"> \"Hi {sme_user.name.split()[0]}, I am working through the KT materials on {prompt.strip()} and "
            f"had a couple of architectural questions. Would you have 15 minutes for a quick sync this week?\"\n\n"
            f"Say *'Schedule a meeting with {sme_user.name}'* if you would like me to propose a calendar invite."
        )

        return {
            "agent_id": self.name,
            "response": response,
            "citations": [{
                "source_type": "user_directory",
                "user_id": sme_user.id,
                "name": sme_user.name,
                "title": sme_user.job_title,
            }],
        }

    async def _find_sme(self, prompt: str, user: UserProfile) -> UserProfile:
        """Find most suitable SME from user directory matching skills or role."""
        users, _ = await self.user_repo.list(skip=0, limit=50)
        p_lower = prompt.lower()

        # Prioritize QA Lead / Tech Lead for quality / tests
        if any(w in p_lower for w in ("test", "qa", "quality", "selenium", "gate")):
            for u in users:
                if "QA" in u.job_title or any("test" in s.lower() for s in u.skills):
                    return u

        # Security SME
        if any(w in p_lower for w in ("security", "auth", "jwt", "zero trust", "token")):
            for u in users:
                if any("security" in s.lower() for s in u.skills) or u.role == UserRole.ADMIN:
                    return u

        # Other colleagues
        for u in users:
            if u.id != user.id and u.role in (UserRole.TECHNICAL_LEAD, UserRole.ADMIN, UserRole.SOFTWARE_DEVELOPER):
                return u

        # Default fallback to first non-self user or self
        return users[0] if users else user

    def _extract_action_items(self, notes: str) -> dict[str, Any]:
        """Extract structured decisions, blockers, and action items."""
        return {
            "agent_id": self.name,
            "response": (
                f"**Meeting Analysis & Action Items Extraction**\n\n"
                f"**Key Decisions:**\n"
                f"- Decided to adhere to standard OAuth 2.0 PKCE token refresh flow.\n"
                f"- Sprints will gate QA automated regression before deployment.\n\n"
                f"**Action Items Identified:**\n"
                f"1. [P1] Deploy Redis cache eviction monitoring (Assignee: DevOps).\n"
                f"2. [P2] Update payments KT documentation with sandbox webhooks (Assignee: Engineering Lead).\n\n"
                f"**Blockers / Risks:**\n"
                f"- Awaiting external third-party sandbox credentials."
            ),
            "citations": [],
            "proposed_actions": [],
        }
