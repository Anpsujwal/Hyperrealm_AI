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
        Orchestrate dynamic multi-agent collaboration across all four specialist agents:
        Knowledge, Insights, Collaborate, and Onboard.
        1. Ensure conversation persistence.
        2. Analyze user intent to dynamically plan required agent execution pipeline.
        3. Dynamically execute agents with inter-agent context passing and delegation.
        4. Prevent delegation loops (cycle detection and max depth).
        5. Synthesize unified response clearly showing each agent's contribution.
        6. Enforce permissions and present proposed actions for explicit user confirmation.
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
            conv = await self.conv_repo.get(conv_id)
            if not conv or conv.user_id != user.id:
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

        # 2. Plan dynamic agent pipeline based on user intent
        pipeline = self._plan_agent_pipeline(prompt, attachments, manual_agent)

        # 3. Dynamic multi-agent execution loop with inter-agent context passing & loop prevention
        executed_agents: list[str] = []
        agent_results: dict[str, dict[str, Any]] = {}
        visited_agents: set[str] = set()
        queue: list[str] = list(pipeline)
        max_delegation_depth = 4

        citations: list[dict[str, Any]] = []
        proposed_actions: list[dict[str, Any]] = []
        discrepancy_notices: list[str] = []
        compliance_report = None
        is_simulated = settings.is_demo

        accumulated_context: dict[str, Any] = {
            "initial_prompt": prompt,
            "user_id": user.id,
            "user_name": user.name,
            "user_role": user.role.value if hasattr(user.role, "value") else str(user.role),
        }

        while queue and len(executed_agents) < max_delegation_depth:
            agent_id = queue.pop(0)

            # Cycle prevention: prevent delegation loops
            if agent_id in visited_agents:
                logger.warning("Delegation loop detected for agent '%s'; skipping to prevent recursive cycle.", agent_id)
                continue
            visited_agents.add(agent_id)

            try:
                if agent_id == "knowledge":
                    res = await self.knowledge_agent.execute(prompt, user, context=accumulated_context)
                elif agent_id == "insights":
                    res = await self.insights_agent.execute(prompt, user, attachments=attachments, context=accumulated_context)
                elif agent_id == "collaborate":
                    res = await self.collaborate_agent.execute(prompt, user, context=accumulated_context)
                elif agent_id == "onboard":
                    res = await self.onboard_agent.execute(prompt, user, context=accumulated_context)
                else:
                    logger.warning("Unknown agent id '%s'; defaulting to Knowledge Agent.", agent_id)
                    res = await self.knowledge_agent.execute(prompt, user, context=accumulated_context)
                    agent_id = "knowledge"
            except Exception as exc:
                logger.exception("Specialist agent '%s' failed during dynamic execution: %s", agent_id, exc)
                res = {
                    "agent_id": agent_id,
                    "response": (
                        f"The {agent_id.title()} Specialist Agent encountered an unexpected processing condition: {exc}. "
                        f"Grounded response was safely isolated."
                    ),
                    "citations": [],
                    "proposed_actions": [],
                }

            agent_results[agent_id] = res
            executed_agents.append(agent_id)
            if res.get("is_simulated") is not None:
                is_simulated = res.get("is_simulated")

            # Enrich accumulated context for subsequent specialist agents
            accumulated_context[f"{agent_id}_findings"] = res.get("response", "")
            if agent_id == "onboard":
                accumulated_context["onboard_topic"] = "Onboarding Path & Compliance Goals"
            elif agent_id == "insights":
                accumulated_context["incident_topic"] = "Technical Diagnostics & Proposal Review"

            # Aggregate citations
            for cit in res.get("citations", []):
                # Avoid duplicates
                if not any(c.get("title") == cit.get("title") and c.get("source_type") == cit.get("source_type") for c in citations):
                    citations.append(cit)

            # Aggregate proposed actions
            for act in res.get("proposed_actions", []):
                proposed_actions.append(act)

            # Aggregate discrepancy notices
            discrepancies = res.get("discrepancies", [])
            if discrepancies:
                discrepancy_notices.extend(discrepancies)

            # Capture compliance report
            if res.get("compliance_report"):
                compliance_report = res.get("compliance_report")

            # Check if specialist agent requested delegation to another agent
            delegate_to = res.get("delegate_to")
            if delegate_to and delegate_to not in visited_agents and delegate_to not in queue:
                logger.info("Agent '%s' dynamically delegated task to '%s'", agent_id, delegate_to)
                queue.append(delegate_to)

        # 4. Synthesize final response
        agent_names = {
            "knowledge": "Knowledge Specialist Agent",
            "insights": "Insights & Architecture Agent",
            "collaborate": "Collaborate & Team Agent",
            "onboard": "Onboard & Learning Agent",
        }

        # If a single agent executed, present its focused response directly
        if len(executed_agents) == 1:
            primary_agent = executed_agents[0]
            response_text = agent_results[primary_agent].get("response", "No response generated.")
            primary_agent_name = agent_names.get(primary_agent, "Specialist Agent")
        else:
            # Multi-agent collaboration: combine contributions with clear attribution headers
            # Set primary agent as the last acting agent or collaborate agent if present
            primary_agent = "collaborate" if "collaborate" in executed_agents else executed_agents[0]
            primary_agent_name = "Central Multi-Agent Orchestrator"

            section_headers = {
                "onboard": "🎓 Onboarding & Learning Specialist",
                "insights": "🔍 Insights & Architecture Specialist",
                "knowledge": "📘 Knowledge Specialist",
                "collaborate": "🤝 Collaboration & Team Specialist",
            }

            contributions = []
            for aid in executed_agents:
                head = section_headers.get(aid, f"Specialist Agent ({aid.title()})")
                text = agent_results[aid].get("response", "").strip()
                contributions.append(f"### {head}\n\n{text}")

            response_text = "\n\n---\n\n".join(contributions)

        discrepancy_notice = " ".join(discrepancy_notices) if discrepancy_notices else None

        # 5. Persist assistant response
        await self.conv_repo.add_message(
            Message(
                id=new_id("msg_"),
                conversation_id=conv_id,
                role="assistant",
                content=response_text,
                agent_id=primary_agent,
                metadata={
                    "citations_count": len(citations),
                    "has_actions": bool(proposed_actions),
                    "delegated_agents": executed_agents,
                },
            )
        )

        return ChatOrchestratorResponse(
            conversation_id=conv_id,
            agent_id=primary_agent,
            agent_name=primary_agent_name,
            response=response_text,
            citations=citations,
            discrepancy_notice=discrepancy_notice,
            compliance_report=compliance_report,
            proposed_actions=proposed_actions,
            workflow_status="pending_approval" if proposed_actions else "completed",
            is_simulated=is_simulated,
            model_used=settings.GEMINI_MODEL,
            delegated_agents=executed_agents,
        )

    def _plan_agent_pipeline(
        self,
        prompt: str,
        attachments: Optional[list[dict[str, Any]]],
        manual_agent: Optional[str] = None,
    ) -> list[str]:
        """
        Dynamically plan agent execution pipeline based on query intent.
        Selects only the necessary agents and establishes the optimal execution order.
        """
        # Manual override: user explicitly chose a specific specialist agent
        if manual_agent and manual_agent != "auto":
            return [manual_agent]

        has_images = bool(attachments and any(a.get("type", "").startswith("image") for a in attachments))
        p = prompt.lower()

        # Intent capabilities detection
        onboard_needed = any(w in p for w in ("onboard", "learning", "training", "course", "curriculum", "path", "orientation", "new hire", "journey", "forms", "checklist", "week 1", "first day"))
        collab_needed = any(w in p for w in ("schedule", "meeting", "meet", "calendar", "who knows", "find expert", "sme", "connect with", "agenda", "scrum", "manager", "1:1", "sync with", "invite"))
        insights_needed = has_images or any(w in p for w in ("evaluate", "review proposal", "error", "incident", "exception", "brand audit", "compliance", "log", "stack trace", "risk", "504", "500", "crash", "bug", "failure", "troubleshoot", "defect"))
        knowledge_needed = any(w in p for w in ("guideline", "documentation", "doc", "kt", "policy", "standard", "knowledge hub", "summarize", "personal notes", "how do i", "what is", "architecture standard"))

        # Multi-Agent Coordination Scenarios:
        # Scenario A: Onboarding inquiry requesting a meeting/sync -> Onboard first, then Collaborate
        if onboard_needed and collab_needed:
            return ["onboard", "collaborate"]

        # Scenario B: Technical issue + guidelines check + expert meeting -> Insights, then Knowledge, then Collaborate
        if insights_needed and knowledge_needed and collab_needed:
            return ["insights", "knowledge", "collaborate"]

        # Scenario C: Technical issue + guidelines check -> Insights, then Knowledge
        if insights_needed and knowledge_needed:
            return ["insights", "knowledge"]

        # Scenario D: Technical issue + expert meeting -> Insights, then Collaborate
        if insights_needed and collab_needed:
            return ["insights", "collaborate"]

        # Scenario E: Knowledge retrieval + follow-up meeting -> Knowledge, then Collaborate
        if knowledge_needed and collab_needed:
            return ["knowledge", "collaborate"]

        # Scenario F: Onboarding + knowledge standards lookup -> Onboard, then Knowledge
        if onboard_needed and knowledge_needed:
            return ["onboard", "knowledge"]

        # Single-Agent Focused Execution:
        if onboard_needed:
            return ["onboard"]
        if insights_needed:
            return ["insights"]
        if collab_needed:
            return ["collaborate"]
        if knowledge_needed:
            return ["knowledge"]

        # Default fallback
        return ["knowledge"]

    def _detect_intent(self, prompt: str, attachments: Optional[list[dict[str, Any]]]) -> str:
        """Single-agent backward-compatibility intent detector."""
        pipeline = self._plan_agent_pipeline(prompt, attachments)
        return pipeline[0] if pipeline else "knowledge"


_orchestrator: Optional[HyperrealmOrchestrator] = None


def get_orchestrator() -> HyperrealmOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HyperrealmOrchestrator()
    return _orchestrator
