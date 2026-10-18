"""Tests for Google ADK runtime and Vertex AI / Gemini integration in Hyperrealm."""

import pytest
from backend.app.config import settings
from backend.app.agents import (
    build_hyperrealm_adk_hierarchy,
    get_adk_runner,
    get_orchestrator,
    HAS_GOOGLE_ADK,
    HAS_GOOGLE_GENAI,
)
from backend.app.agents.adk_runtime import (
    search_personal_and_official_knowledge,
    get_official_guideline_clause,
    investigate_incident_logs,
    evaluate_technical_proposal,
    discover_subject_matter_experts,
    propose_team_meeting_action,
    recommend_role_onboarding_modules,
)


from backend.app.schemas import ChatOrchestratorRequest


def test_adk_flags_and_imports():
    """Verify ADK and GenAI libraries or fallback mocks are cleanly loaded without raising errors."""
    assert HAS_GOOGLE_ADK is True
    assert HAS_GOOGLE_GENAI is True


def test_build_hyperrealm_adk_hierarchy():
    """Verify the Google ADK hierarchy creates the root orchestrator and 4 sub-agents."""
    root, specialists = build_hyperrealm_adk_hierarchy(model_name=settings.GEMINI_MODEL)
    
    assert root is not None
    assert root.name == "hyperrealm_orchestrator"
    assert root.model == settings.GEMINI_MODEL
    
    # Sub-agents check
    sub_agents = root.sub_agents
    assert len(sub_agents) == 4
    sub_names = {agent.name for agent in sub_agents}
    assert sub_names == {
        "knowledge_agent",
        "insights_agent",
        "collaborate_agent",
        "onboard_agent",
    }
    
    # Verify each specialist agent exists in specialists list
    spec_names = {agent.name for agent in specialists}
    assert "knowledge_agent" in spec_names
    assert "insights_agent" in spec_names
    assert "collaborate_agent" in spec_names
    assert "onboard_agent" in spec_names


def test_get_adk_runner():
    """Verify that get_adk_runner constructs an InMemoryRunner with the root agent."""
    runner = get_adk_runner(model_name=settings.GEMINI_MODEL)
    assert runner is not None
    assert runner.agent.name == "hyperrealm_orchestrator"


def test_adk_tool_functions():
    """Verify the ADK domain tool bindings execute deterministically and return rich data."""
    # 1. Search knowledge tool
    res_k = search_personal_and_official_knowledge("security policy authentication")
    assert "Security Standards" in res_k
    assert "Brand Identity" in res_k

    # 2. Get guideline clause
    res_g_sec = get_official_guideline_clause("security")
    assert "Security Standards" in res_g_sec
    res_g_brand = get_official_guideline_clause("brand")
    assert "Brand Identity" in res_g_brand

    # 3. Investigate incident logs
    res_i = investigate_incident_logs("payments")
    assert "INC-402" in res_i

    # 4. Evaluate proposal
    res_p = evaluate_technical_proposal("Migrate legacy auth to biometric Passkeys and WebAuthn")
    assert "zero-trust" in res_p

    # 5. Discover SMEs
    res_sme = discover_subject_matter_experts("Payments")
    assert "Carol Wu" in res_sme

    # 6. Propose meeting action
    res_m = propose_team_meeting_action("Sprint Alignment", "user_1, user_priya")
    assert "Sprint Alignment" in res_m

    # 7. Recommend onboarding
    res_o = recommend_role_onboarding_modules("Backend Engineer")
    assert "Curriculum for Backend Engineer" in res_o


def test_orchestrator_adk_integration():
    """Verify HyperrealmOrchestrator exposes the ADK hierarchy and runner."""
    orchestrator = get_orchestrator()
    assert orchestrator.adk_root_agent is not None
    assert orchestrator.adk_root_agent.name == "hyperrealm_orchestrator"
    assert len(orchestrator.adk_specialist_agents) == 4
    assert orchestrator.adk_runner is not None


from backend.app.models import UserProfile, UserRole


@pytest.mark.asyncio
async def test_demo_mode_preserves_deterministic_fallback():
    """Verify that in demo mode (default), route_and_execute runs deterministically and does not fail."""
    orchestrator = get_orchestrator()
    
    # Ensure is_demo is True
    assert settings.is_demo is True
    
    user = UserProfile(
        id="usr_002",
        email="engineer@hyperrealm.internal",
        name="Carol Wu",
        role=UserRole.TECHNICAL_LEAD,
        department_name="Engineering",
        job_title="Technical Lead",
    )
    
    response = await orchestrator.route_and_execute(
        prompt="What are the security guidelines for authentication?",
        user=user,
    )
    
    assert response.agent_name == "Knowledge Specialist Agent"
    assert response.model_used == settings.GEMINI_MODEL
    assert response.is_simulated is True
    assert len(response.response) > 50


