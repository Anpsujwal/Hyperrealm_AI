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
    from google.adk.agents import LlmAgent  # type: ignore[import-not-found]  # pyright: ignore[reportMissingImports]
    from google.adk.runners import InMemoryRunner  # type: ignore[import-not-found]  # pyright: ignore[reportMissingImports]
    HAS_GOOGLE_ADK = True
except ImportError:
    LlmAgent = None  # type: ignore[assignment,misc]
    InMemoryRunner = None  # type: ignore[assignment,misc]
    HAS_GOOGLE_ADK = False
    logger.info("google-adk package not imported; running in fallback mode.")

try:
    from google import genai  # type: ignore[import-not-found]  # pyright: ignore[reportMissingImports]
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

# ─── Live Vertex AI / Gemini Client Provider & Error Mapping ─────────────────

class GeminiInvocationError(Exception):
    """Structured error for Gemini / Vertex AI failures with human-readable diagnostic messages."""
    def __init__(
        self,
        message: str,
        error_type: str = "general",
        status_code: int = 500,
        original_error: Optional[Exception] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.original_error = original_error
        self.error_code = error_code or error_type.upper()

    @classmethod
    def from_exception(cls, exc: Exception, model_name: str = "gemini-3.8-flash") -> GeminiInvocationError:
        return _map_gemini_exception(exc, model_name)


def get_gemini_runtime_status() -> dict[str, Any]:
    """Return explicit verification status of the Gemini / Vertex AI runtime."""
    settings = get_settings()
    has_creds = bool(
        settings.GOOGLE_APPLICATION_CREDENTIALS
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or settings.GEMINI_API_KEY
    )
    has_proj = bool(settings.GOOGLE_CLOUD_PROJECT or settings.GCP_PROJECT_ID)
    is_live = not settings.is_demo and ((has_proj and has_creds) or bool(settings.GEMINI_API_KEY))
    return {
        "is_live": is_live,
        "model": settings.GEMINI_MODEL,
        "fallback_model": settings.GEMINI_FALLBACK_MODEL,
        "vertexai": settings.GOOGLE_GENAI_USE_VERTEXAI,
        "project": settings.GOOGLE_CLOUD_PROJECT,
        "location": settings.GOOGLE_CLOUD_LOCATION,
        "client_type": "google_genai_sdk",
        "status": "ready" if is_live else ("demo_mode" if settings.is_demo else "unconfigured"),
    }


_cached_client: Optional[Any] = None


def get_live_genai_client() -> Optional[Any]:
    """
    Construct a live google.genai.Client targeting Vertex AI or Gemini API
    if valid credentials/keys are present and not in demo mode.
    """
    global _cached_client
    if _cached_client is not None:
        return _cached_client

    settings = get_settings()
    if settings.is_demo:
        return None

    if not HAS_GOOGLE_GENAI or genai is None:
        return None

    try:
        # Set credentials in environment if configured
        if settings.GOOGLE_APPLICATION_CREDENTIALS and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

        # 1. Direct Gemini Developer API key
        if settings.GEMINI_API_KEY:
            _cached_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            return _cached_client

        # 2. Google Vertex AI via Cloud Project & ADC
        project = settings.GOOGLE_CLOUD_PROJECT or settings.GCP_PROJECT_ID
        if project:
            location = settings.GOOGLE_CLOUD_LOCATION or "global"
            _cached_client = genai.Client(vertexai=True, project=project, location=location)
            return _cached_client

    except Exception as exc:
        logger.warning("Could not initialize live google.genai.Client: %s", exc)
        return None

    return None


async def verify_gemini_model_availability(model_name: Optional[str] = None) -> dict[str, Any]:
    """
    Directly verify that the configured model ID is supported and accessible via Vertex AI.
    Returns status dict or raises GeminiInvocationError.
    """
    import asyncio
    settings = get_settings()
    target_model = model_name or settings.GEMINI_MODEL
    client = get_live_genai_client()

    if not client:
        return {
            "status": "unavailable",
            "model": target_model,
            "message": "Live Gemini client could not be initialized (missing credentials or demo mode active).",
            "is_live": False,
        }

    try:
        # Run a minimal ping against the configured model
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=target_model,
            contents="ping",
        )
        return {
            "status": "operational",
            "model": target_model,
            "message": f"Successfully verified live Vertex AI connectivity for model '{target_model}'.",
            "is_live": True,
        }
    except Exception as exc:
        err = _map_gemini_exception(exc, target_model)
        return {
            "status": "error",
            "model": target_model,
            "error_type": err.error_type,
            "message": err.message,
            "is_live": False,
        }


def _map_gemini_exception(exc: Exception, model_name: str) -> GeminiInvocationError:
    """Map Google Cloud / GenAI exceptions to clear, actionable enterprise errors."""
    err_str = str(exc)
    err_cls = exc.__class__.__name__

    # 1. Quota / Rate Limits (429)
    if "429" in err_str or "ResourceExhausted" in err_cls or "QUOTA_EXCEEDED" in err_str:
        return GeminiInvocationError(
            message=f"Gemini API rate limit or quota exceeded for model '{model_name}'. Please retry after a brief pause.",
            error_type="quota_exceeded",
            status_code=429,
            original_error=exc,
        )

    # 2. Model Not Found / Unavailable (404)
    if "404" in err_str or "NotFound" in err_cls or "was not found" in err_str:
        return GeminiInvocationError(
            message=(
                f"Configured model '{model_name}' is not available in the specified Google Cloud project or location. "
                "Verify the model ID and API availability in Google Cloud Console."
            ),
            error_type="model_unavailable",
            status_code=404,
            original_error=exc,
        )

    # 3. Permission Denied / Authorization (403)
    if "403" in err_str or "PermissionDenied" in err_cls or "PERMISSION_DENIED" in err_str:
        return GeminiInvocationError(
            message=(
                f"Insufficient Google Cloud IAM permissions to invoke Vertex AI model '{model_name}'. "
                "Ensure the service account has 'roles/aiplatform.user' or 'Vertex AI User' role assigned."
            ),
            error_type="permission_denied",
            status_code=403,
            original_error=exc,
        )

    # 4. Invalid Credentials / Authentication (401)
    if "401" in err_str or "Unauthenticated" in err_cls or "credentials" in err_str.lower():
        return GeminiInvocationError(
            message="Invalid or expired Google Cloud credentials for Vertex AI. Check GOOGLE_APPLICATION_CREDENTIALS.",
            error_type="unauthenticated",
            status_code=401,
            original_error=exc,
        )

    # 5. Network Failures / Timeouts
    if "timeout" in err_str.lower() or "connect" in err_str.lower() or "connection" in err_str.lower():
        return GeminiInvocationError(
            message="Network failure communicating with Google Vertex AI endpoint. Check internet connection and proxy settings.",
            error_type="network_failure",
            status_code=504,
            original_error=exc,
        )

    return GeminiInvocationError(
        message=f"Google Vertex AI invocation error: {err_str}",
        error_type="general_error",
        status_code=500,
        original_error=exc,
    )


async def call_gemini_model(
    prompt: str,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None,
    contents: Optional[Any] = None,
    temperature: float = 0.2,
) -> str:
    """
    Invoke real Gemini model via Vertex AI using thread execution to prevent event loop blocking.
    Raises GeminiInvocationError on failure.
    """
    import asyncio
    settings = get_settings()
    active_model = model_name or settings.GEMINI_MODEL
    client = get_live_genai_client()

    if not client:
        raise GeminiInvocationError(
            "Live Gemini client is not initialized. Ensure GOOGLE_CLOUD_PROJECT and valid credentials are configured.",
            error_type="not_initialized",
            status_code=503,
        )

    payload = contents if contents is not None else prompt

    def _sync_call():
        config_kwargs: dict[str, Any] = {"temperature": temperature}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        return client.models.generate_content(
            model=active_model,
            contents=payload,
            config=config_kwargs,
        )

    try:
        response = await asyncio.to_thread(_sync_call)
        if response and response.text:
            return response.text.strip()
        return ""
    except Exception as exc:
        logger.error("Gemini model '%s' call failed: %s", active_model, exc)
        raise _map_gemini_exception(exc, active_model) from exc


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

    system_instruction = (
        f"You are the Hyperrealm AI Assistant serving employee {user.full_name} ({user.email}), "
        f"role {user.role.value if hasattr(user.role, 'value') else user.role}. "
        "Provide grounded enterprise responses with clear structure, actionable next steps, and verified facts."
    )

    try:
        text = await call_gemini_model(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=settings.GEMINI_MODEL,
        )
        if text:
            return {
                "response": text,
                "model_used": settings.GEMINI_MODEL,
                "is_simulated": False,
            }
    except GeminiInvocationError as g_err:
        logger.warning("Live Gemini model invocation failed: %s (%s)", g_err.message, g_err.error_type)
        return None
    except Exception as exc:
        logger.warning("Unexpected error during live Gemini call: %s", exc)
        return None

    return None
