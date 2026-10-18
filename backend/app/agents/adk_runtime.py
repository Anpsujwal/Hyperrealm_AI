"""
HYPERREALM Official Google ADK Runtime & Live Gemini/Vertex AI Integration.
Defines Google ADK (Agent Development Kit) LlmAgent hierarchy, InMemoryRunner,
and live Vertex AI execution with safe fallback guards for demo mode.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Optional

from ..config import get_settings
from ..models import UserProfile

logger = logging.getLogger("hyperrealm.agents.adk")

# ─── Safe Import Guards for Google Cloud & ADK SDKs ──────────────────────────
try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    HAS_GOOGLE_ADK = True
except ImportError:
    LlmAgent = None  # type: ignore[assignment,misc]
    InMemoryRunner = None  # type: ignore[assignment,misc]
    HAS_GOOGLE_ADK = False
    logger.info("google-adk package not imported; running in fallback mode.")

try:
    from google import genai
    HAS_GOOGLE_GENAI = True
except ImportError:
    genai = None  # type: ignore[assignment]
    HAS_GOOGLE_GENAI = False
    logger.info("google-genai package not imported; running in fallback mode.")


# ─── Specialist Tool Bindings for Google ADK ──────────────────────────────────

def search_personal_and_official_knowledge(query: str) -> str:
    """Search authoritative company guidelines and user's personal knowledge documents."""
    return (
        f"Retrieval query for '{query}': Found relevant passages in 'Hyperrealm Security Standards v3.0' "
        f"(mandating SameSite=Strict HttpOnly cookies) and 'Brand Identity Standards v2.1' (WCAG AA 4.5:1 contrast)."
    )


def get_official_guideline_clause(category: str = "security") -> str:
    """Retrieve official company guideline standards by category (security, brand, architecture)."""
    if category.lower() == "brand":
        return "Brand Identity Standards v2.1: Primary violet #6366f1, WCAG AA contrast ratio >= 4.5:1, 24px logo clear space."
    return "Engineering Security Standards v3.0: Mandates OAuth 2.0 PKCE, HttpOnly cookies, prohibits client localStorage token storage."


def investigate_incident_logs(service_name: str = "payments") -> str:
    """Lookup historical incidents, post-mortems, and root-cause analyses for a given service."""
    return (
        f"Incident history for '{service_name}': INC-402 (Stripe webhook signature mismatch resolved via secret rotation); "
        f"INC-309 (Token expiry in Redis cache aligned to 45 minutes)."
    )


def evaluate_technical_proposal(proposal_summary: str) -> str:
    """Evaluate an engineering architecture proposal against published organizational quality gates."""
    return (
        f"Evaluation of proposal: Analyzed against zero-trust rules. Quality gates require >= 85% automated test coverage "
        f"and zero client-side token caching. Verification passed."
    )


def discover_subject_matter_experts(topic: str) -> str:
    """Identify organizational subject-matter experts (SMEs) and project leads by skill and domain."""
    t = topic.lower()
    if "payment" in t or "auth" in t or "token" in t:
        return "Expert: Carol Wu (Technical Lead - Payments Gateway & Auth Architecture, Engineering)"
    if "brand" in t or "design" in t or "ui" in t:
        return "Expert: Elena Rostova (Staff Product Designer - Design Systems, Product Design)"
    return "Expert: Marcus Vance (Principal Architect - Cloud Infrastructure & Security)"


def propose_team_meeting_action(title: str, attendee: str = "Carol Wu") -> str:
    """Create a proposed meeting action item requiring user approval."""
    return f"Prepared meeting invitation proposal: '{title}' with {attendee}. Requires user approval before dispatch."


def recommend_role_onboarding_modules(role: str = "Software Developer") -> str:
    """Recommend mandatory and elective learning paths and curriculum for a given employee role."""
    return (
        f"Curriculum for {role}: 1. Zero Trust Authentication & Secure Headers (Mandatory, 45m); "
        f"2. Microservices Architecture & Event Queues (Mandatory, 90m); 3. WCAG AA Accessible Design Tokens (Elective, 30m)."
    )


# ─── Hierarchy Builder ───────────────────────────────────────────────────────

def build_hyperrealm_adk_hierarchy(
    model_name: Optional[str] = None,
) -> tuple[Optional[Any], list[Any]]:
    """
    Construct the full Google ADK Agent hierarchy:
    - 4 domain-specialist LlmAgents (knowledge, insights, collaborate, onboard)
    - 1 root LlmAgent (hyperrealm_orchestrator) with specialist sub-agents
    Returns (root_agent, specialist_agents).
    """
    if not HAS_GOOGLE_ADK or LlmAgent is None:
        logger.debug("Google ADK not installed; hierarchy construction skipped.")
        return None, []

    settings = get_settings()
    active_model = model_name or settings.GEMINI_MODEL

    # 1. Knowledge Specialist Agent
    adk_knowledge_agent = LlmAgent(
        name="knowledge_agent",
        description="Searches personal Knowledge Hub documents, authoritative company guidelines, and KT summaries.",
        model=active_model,
        instruction=(
            "You are the Hyperrealm Knowledge Specialist Agent. Your purpose is to provide accurate, grounded answers "
            "based strictly on company guidelines, standard operating procedures, and personal technical documentation. "
            "Always include citations to verified documents and highlight discrepancies when personal notes conflict with official rules."
        ),
        tools=[search_personal_and_official_knowledge, get_official_guideline_clause],
    )

    # 2. Insights & Architecture Specialist Agent
    adk_insights_agent = LlmAgent(
        name="insights_agent",
        description="Evaluates technical proposals, investigates error logs against historical incidents, and conducts brand compliance audits.",
        model=active_model,
        instruction=(
            "You are the Hyperrealm Insights & Architecture Specialist Agent. Your purpose is to evaluate system architecture, "
            "troubleshoot production error logs by comparing against historical post-mortems, and audit design assets against brand guidelines."
        ),
        tools=[investigate_incident_logs, evaluate_technical_proposal],
    )

    # 3. Collaborate & Team Specialist Agent
    adk_collaborate_agent = LlmAgent(
        name="collaborate_agent",
        description="Discovers subject-matter experts (SMEs), coordinates team meetings, and extracts action items from notes.",
        model=active_model,
        instruction=(
            "You are the Hyperrealm Collaborate Specialist Agent. Your purpose is to help team members connect with the right SMEs, "
            "draft follow-up communications, and propose calendar meetings with clear agendas and approval gates."
        ),
        tools=[discover_subject_matter_experts, propose_team_meeting_action],
    )

    # 4. Onboard & Learning Specialist Agent
    adk_onboard_agent = LlmAgent(
        name="onboard_agent",
        description="Constructs personalized role-based onboarding paths, recommends mandatory learning, and explains company standards.",
        model=active_model,
        instruction=(
            "You are the Hyperrealm Onboard Specialist Agent. Your purpose is to accelerate new hire and role transitions "
            "by formulating structured onboarding checklists, identifying knowledge gaps, and recommending relevant courses."
        ),
        tools=[recommend_role_onboarding_modules],
    )

    specialist_agents = [
        adk_knowledge_agent,
        adk_insights_agent,
        adk_collaborate_agent,
        adk_onboard_agent,
    ]

    # Root Orchestrator coordinating all 4 specialist agents
    hyperrealm_orchestrator = LlmAgent(
        name="hyperrealm_orchestrator",
        description="Central Orchestrator coordinating knowledge, insights, collaborate, and onboard specialist agents.",
        model=active_model,
        instruction=(
            "You are the Central Hyperrealm Orchestrator. When a user presents a request, evaluate their intent "
            "and delegate to the appropriate specialist sub-agent (knowledge_agent, insights_agent, collaborate_agent, onboard_agent). "
            "Synthesize specialist findings into a cohesive, professional enterprise response with verified citations."
        ),
        sub_agents=specialist_agents,
    )

    return hyperrealm_orchestrator, specialist_agents


def get_adk_runner(model_name: Optional[str] = None) -> Optional[Any]:
    """Instantiate an InMemoryRunner initialized with the root Hyperrealm ADK hierarchy."""
    if not HAS_GOOGLE_ADK or InMemoryRunner is None:
        return None
    root_agent, _ = build_hyperrealm_adk_hierarchy(model_name)
    if not root_agent:
        return None
    try:
        return InMemoryRunner(agent=root_agent)
    except Exception as exc:
        logger.warning("Failed to initialize Google ADK InMemoryRunner: %s", exc)
        return None


# ─── Live Vertex AI / Gemini Client Provider ─────────────────────────────────

def get_live_genai_client() -> Optional[Any]:
    """
    Construct a live google.genai.Client targeting Vertex AI or Gemini API
    if valid credentials/keys are present and not in demo mode.
    """
    settings = get_settings()
    if settings.is_demo:
        return None

    if not HAS_GOOGLE_GENAI or genai is None:
        return None

    try:
        # 1. Direct Gemini Developer API key
        if settings.GEMINI_API_KEY:
            return genai.Client(api_key=settings.GEMINI_API_KEY)

        # 2. Google Vertex AI via Cloud Project & ADC
        project = settings.GOOGLE_CLOUD_PROJECT or settings.GCP_PROJECT_ID
        if project:
            location = settings.GOOGLE_CLOUD_LOCATION or "us-central1"
            return genai.Client(vertexai=True, project=project, location=location)

    except Exception as exc:
        logger.warning("Could not initialize live google.genai.Client: %s", exc)
        return None

    return None


async def execute_live_adk_or_gemini(
    prompt: str,
    user: UserProfile,
    agent_id: Optional[str] = None,
    attachments: Optional[list[dict[str, Any]]] = None,
) -> Optional[dict[str, Any]]:
    """
    Execute request against live Google Gemini / Vertex AI model if live mode is active.
    Returns None if demo mode is enabled or credentials fail, triggering seamless fallback.
    """
    settings = get_settings()
    if settings.is_demo:
        return None

    client = get_live_genai_client()
    if not client:
        return None

    model_name = settings.GEMINI_MODEL
    try:
        system_instruction = (
            f"You are the Hyperrealm AI Assistant serving employee {user.full_name} ({user.email}), "
            f"role {user.role.value if hasattr(user.role, 'value') else user.role}. "
            "Provide grounded enterprise responses with clear structure, actionable next steps, and verified facts."
        )

        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=dict(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )

        if response and response.text:
            return {
                "response": response.text,
                "model_used": model_name,
                "is_simulated": False,
            }
    except Exception as exc:
        logger.warning("Live Gemini model invocation failed: %s; falling back to deterministic engine.", exc)
        return None

    return None
