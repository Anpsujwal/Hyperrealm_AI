"""
HYPERREALM Central Orchestrator (base_orchestrator.py).
Coordinates the four specialist agents, maintains conversation context,
routes requests based on intent or manual selection, gathers citations,
and interfaces with Validation & Approval for proposed actions.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import get_settings
from ..dependencies import get_conv_repo
from ..models import (
    Conversation,
    DocumentScope,
    Message,
    UserProfile,
    new_id,
    utcnow,
)
from ..schemas import ChatOrchestratorResponse
from ..services.retrieval import EnterpriseRetrievalService
from ..services.workflow import WorkflowService
from .adk_runtime import (
    HAS_GOOGLE_ADK,
    HAS_GOOGLE_GENAI,
    build_hyperrealm_adk_hierarchy,
    execute_live_adk_or_gemini,
    get_adk_runner,
)
from .collaborate_agent import CollaborateAgent
from .insights_agent import InsightsAgent
from .knowledge_agent import KnowledgeAgent
from .onboard_agent import OnboardAgent

logger = logging.getLogger("hyperrealm.orchestrator")


class HyperrealmOrchestrator:
    """
    Central coordinator orchestrating Knowledge, Insights, Collaborate,
    and Onboard specialist agents through shared backend services and Google ADK.
    """

    def __init__(self):
        self.retrieval = EnterpriseRetrievalService()
        self.workflow = WorkflowService()

        # Specialist agents
        self.knowledge_agent = KnowledgeAgent(self.retrieval)
        self.insights_agent = InsightsAgent(self.retrieval)
        self.collaborate_agent = CollaborateAgent(self.retrieval, self.workflow)
        self.onboard_agent = OnboardAgent(self.retrieval)

        # Official Google ADK Agent Hierarchy & In-Memory Runner
        self.adk_root_agent, self.adk_specialist_agents = build_hyperrealm_adk_hierarchy()
        self.adk_runner = get_adk_runner()

    @property
    def conv_repo(self):
        return get_conv_repo()

    async def route_and_execute(
        self,
        prompt: str,
        user: UserProfile,
        conversation_id: Optional[str] = None,
        manual_agent: Optional[str] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
    ) -> ChatOrchestratorResponse:
        """
        Orchestrate request execution:
        1. Ensure conversation exists; persist user prompt.
        2. Determine active agent(s): manual override or automatic intent detection.
        3. Delegate to specialist agent(s) with authorized context.
        4. Synthesize final response with citations, compliance reports, and proposed actions.
        5. Persist assistant response message.
        """
        settings = get_settings()

        # 1. Manage conversation persistence
        conv_id = conversation_id
        if not conv_id:
            title = prompt[:36] + ("..." if len(prompt) > 36 else "")
            new_conv = Conversation(
                id=new_id("conv_"),
                user_id=user.id,
                title=title,
                agent_id=manual_agent or "auto",
            )
            await self.conv_repo.create(new_conv)
            conv_id = new_conv.id
        else:
            # Verify conversation belongs to user
            conv = await self.conv_repo.get(conv_id)
            if not conv or conv.user_id != user.id:
                # If invalid or mismatched, create user's own conversation
                new_conv = Conversation(
                    id=new_id("conv_"),
                    user_id=user.id,
                    title=prompt[:36],
                    agent_id=manual_agent or "auto",
                )
                await self.conv_repo.create(new_conv)
                conv_id = new_conv.id

        # Persist user message
        await self.conv_repo.add_message(
            Message(
                id=new_id("msg_"),
                conversation_id=conv_id,
                role="user",
                content=prompt,
                agent_id=manual_agent or "auto",
            )
        )

        # 2. Determine target agent
        selected_agent = manual_agent if manual_agent and manual_agent != "auto" else self._detect_intent(prompt, attachments)

        # 3. Delegate execution
        agent_result: dict[str, Any] = {}
        discrepancy_notice = None
        compliance_report = None
        proposed_actions = []
        citations = []
        is_simulated = settings.is_demo

        # If live cloud mode is active, attempt live ADK / Vertex AI execution first
        if not settings.is_demo:
            try:
                live_output = await execute_live_adk_or_gemini(
                    prompt=prompt,
                    user=user,
                    agent_id=selected_agent,
                    attachments=attachments,
                )
                if live_output and live_output.get("response"):
                    agent_result = live_output
                    is_simulated = False
            except Exception as live_err:
                logger.warning("Live ADK execution failed, falling back to deterministic agent: %s", live_err)

        if not agent_result:
            try:
                if selected_agent == "knowledge":
                    agent_result = await self.knowledge_agent.execute(prompt, user)
                    citations = agent_result.get("citations", [])
                    discrepancies = agent_result.get("discrepancies", [])
                    if discrepancies:
                        discrepancy_notice = " ".join(discrepancies)

                elif selected_agent == "insights":
                    agent_result = await self.insights_agent.execute(prompt, user, attachments=attachments)
                    citations = agent_result.get("citations", [])
                    compliance_report = agent_result.get("compliance_report")

                elif selected_agent == "collaborate":
                    agent_result = await self.collaborate_agent.execute(prompt, user)
                    citations = agent_result.get("citations", [])
                    proposed_actions = agent_result.get("proposed_actions", [])

                elif selected_agent == "onboard":
                    agent_result = await self.onboard_agent.execute(prompt, user)
                    citations = agent_result.get("citations", [])

                else:
                    # Multi-agent or central synthesis fallback
                    agent_result = await self.knowledge_agent.execute(prompt, user)
                    citations = agent_result.get("citations", [])
                    selected_agent = "knowledge"

            except Exception as e:
                logger.exception("Specialist agent execution failed: %s", e)
                agent_result = {
                    "agent_id": selected_agent,
                    "response": (
                        f"The {selected_agent.title()} Agent encountered an unexpected processing condition: {e}. "
                        f"Grounded response was safely terminated to prevent invalid recommendations."
                    ),
                }

        response_text = agent_result.get("response", "No response generated.")

        # Persist assistant message
        await self.conv_repo.add_message(
            Message(
                id=new_id("msg_"),
                conversation_id=conv_id,
                role="assistant",
                content=response_text,
                agent_id=selected_agent,
                metadata={"citations_count": len(citations), "has_actions": bool(proposed_actions)},
            )
        )

        agent_names = {
            "knowledge": "Knowledge Specialist Agent",
            "insights": "Insights & Architecture Agent",
            "collaborate": "Collaborate & Team Agent",
            "onboard": "Onboard & Learning Agent",
        }

        return ChatOrchestratorResponse(
            conversation_id=conv_id,
            agent_id=selected_agent,
            agent_name=agent_names.get(selected_agent, "Central Orchestrator"),
            response=response_text,
            citations=citations,
            discrepancy_notice=discrepancy_notice,
            compliance_report=compliance_report,
            proposed_actions=proposed_actions,
            workflow_status="pending_approval" if proposed_actions else "completed",
            is_simulated=is_simulated,
            model_used=settings.GEMINI_MODEL,
        )

    def _detect_intent(self, prompt: str, attachments: Optional[list[dict[str, Any]]]) -> str:
        """Analyze user query and attachments to route to the optimal specialist agent."""
        # Visual assets or brand compliance -> Insights Agent
        if attachments and any(a.get("type", "").startswith("image") for a in attachments):
            return "insights"

        p = prompt.lower()

        # Onboarding & Learning keywords
        if any(w in p for w in ("onboard", "learning", "training", "course", "curriculum", "path", "orientation")):
            return "onboard"

        # Collaboration & Calendar & Meetings keywords
        if any(w in p for w in ("schedule", "meeting", "meet", "calendar", "who knows", "find expert", "sme", "connect with", "agenda", "scrum")):
            return "collaborate"

        # Insights & Evaluation & Errors keywords
        if any(w in p for w in ("evaluate", "review proposal", "error", "incident", "exception", "brand audit", "compliance", "log", "stack trace", "risk")):
            return "insights"

        # Default knowledge retrieval (KT documents, personal library, guidelines)
        return "knowledge"


_orchestrator: Optional[HyperrealmOrchestrator] = None


def get_orchestrator() -> HyperrealmOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HyperrealmOrchestrator()
    return _orchestrator
