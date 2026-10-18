# HYPERREALM Specialist Agents Package

This directory contains the four specialist AI agents and the central coordinator powering HYPERREALM.

## Package Structure

```
backend/app/agents/
├── __init__.py               # Package re-exports for all agents and orchestrator
├── base_orchestrator.py      # Central Orchestrator (Intent routing, context gating, synthesis)
├── knowledge_agent.py        # Knowledge Agent (Personal Hub & Official Policy retrieval, citations)
├── insights_agent.py         # Insights Agent (Architecture standards, error analysis, brand audit)
├── collaborate_agent.py      # Collaborate Agent (SME discovery, meeting scheduling, action items)
└── onboard_agent.py          # Onboard Agent (Role-based onboarding curricula & compliance refreshers)
```

## Agent Responsibilities & Delegation Matrix

| Agent | Module | Primary Triggers | Shared Services Used |
| :--- | :--- | :--- | :--- |
| **Central Orchestrator** | `base_orchestrator.py` | Incoming prompt to `/api/v1/chat` | All agents, `retrieval.py`, `workflow.py` |
| **Knowledge Agent** | `knowledge_agent.py` | "What does KT say?", "Explain policy", "Summarize doc" | `retrieval.py` (`personal` & `official` scopes) |
| **Insights Agent** | `insights_agent.py` | "Review design", "Check error log", "Audit brand image" | `retrieval.py` (`historical`), `vision.py` |
| **Collaborate Agent** | `collaborate_agent.py` | "Find expert on...", "Schedule sync", "Draft agenda" | `retrieval.py`, `workflow.py` (actions) |
| **Onboard Agent** | `onboard_agent.py` | "Create onboarding path", "What training do I need?" | `retrieval.py` (`learning`, `official`) |

## Design Principles

1. **Shared Services, Not Silos:** Agents never create separate database connections or file storage layers. All agents consume the shared `EnterpriseRetrievalService`, `BrandComplianceService`, and `WorkflowService`.
2. **Context-Gated Retrieval:** Agents only access documents permitted by the caller's authenticated user ID and role.
3. **Verifiable Citations:** When providing answers grounded in personal documents or official standards, agents return structured citations referencing the document title, scope, version, and quoted text.
4. **Governed Execution:** Consequential operations (e.g. creating meetings, publishing guidelines, updating tasks) are proposed as structured actions and dispatched through the backend Validation & Approval workflow.

For the full architectural breakdown, refer to [backend/README.md](file:///c:/Users/hymat/OneDrive/Desktop/Hyperrealm/backend/README.md).
