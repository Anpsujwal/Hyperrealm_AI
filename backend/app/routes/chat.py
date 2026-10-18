"""
Chat and Agent Orchestration routes.
Exposes the central AI Copilot orchestrator and specialist agent execution endpoints.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..agents.base_orchestrator import get_orchestrator
from ..auth import CurrentUser
from ..models import UserProfile
from ..schemas import ChatOrchestratorRequest, ChatOrchestratorResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatOrchestratorResponse, summary="HYPERREALM AI Copilot Central Chat")
async def chat_orchestrator(
    body: ChatOrchestratorRequest,
    current_user: CurrentUser,
) -> ChatOrchestratorResponse:
    """
    Central AI Copilot endpoint:
    - Coordinates Knowledge, Insights, Collaborate, and Onboard specialist agents.
    - Automatically searches user's personal Knowledge Hub and official guidelines.
    - Grounds responses with citations and identifies conflicting information.
    - Emits proposed actions for Validation & Approval when consequential changes are requested.
    """
    orchestrator = get_orchestrator()
    result = await orchestrator.route_and_execute(
        prompt=body.prompt,
        user=current_user,
        conversation_id=body.conversation_id,
        manual_agent=body.agent_id,
        attachments=body.attachments,
    )
    return result


@router.post("/agents/{agent_name}/execute", response_model=ChatOrchestratorResponse,
             summary="Execute specific specialist agent")
async def execute_agent(
    agent_name: str,
    body: ChatOrchestratorRequest,
    current_user: CurrentUser,
) -> ChatOrchestratorResponse:
    """
    Directly execute one of the four specialist agents:
    - 'knowledge'
    - 'insights'
    - 'collaborate'
    - 'onboard'
    Enforces authorization and security controls.
    """
    valid_agents = {"knowledge", "insights", "collaborate", "onboard"}
    if agent_name.lower() not in valid_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specialist agent '{agent_name}' not found. Supported agents: {', '.join(sorted(valid_agents))}",
        )

    orchestrator = get_orchestrator()
    result = await orchestrator.route_and_execute(
        prompt=body.prompt,
        user=current_user,
        conversation_id=body.conversation_id,
        manual_agent=agent_name.lower(),
        attachments=body.attachments,
    )
    return result
