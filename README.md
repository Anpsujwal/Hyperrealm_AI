# HYPERREALM

Enterprise AI Workspace & Collaborative Platform.

## Project Structure

```
Hyperrealm/
├── frontend/               # Vite + React 19 + TypeScript frontend application
│   ├── src/                # UI components, contexts, pages, design system
│   ├── public/             # Static assets
│   ├── package.json        # Frontend dependencies & build scripts
│   └── vite.config.ts      # Vite configuration
│
├── backend/                # FastAPI 0.115+ modular backend
│   ├── app/                # Core routes, models, agents, services, repositories
│   │   ├── agents/         # Four specialist AI agents & Base Orchestrator
│   │   └── services/       # Ingestion, Enterprise Retrieval, Vision, Workflow
│   ├── tests/              # Pytest test suite (54 automated tests)
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Agent Architecture & Multimodal Knowledge Pipeline
│
├── package.json            # Root workspace runner scripts
└── pyproject.toml          # Pytest configuration
```

> **Agent Architecture & Pipeline Documentation:** Detailed documentation on the Four Specialist AI Agents (Knowledge, Insights, Collaborate, Onboard), Orchestrator, and Knowledge Pipeline is available in [`backend/README.md`](file:///c:/Users/hymat/OneDrive/Desktop/Hyperrealm/backend/README.md).


## Quick Start

### 1. Frontend Development

```bash
# From root
npm run dev

# Or from inside frontend/
cd frontend
npm install
npm run dev
```

### 2. Backend Development

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run backend development server
npm run backend:dev
# (or: uvicorn backend.app.main:app --reload --port 8000)

# Run test suite
npm run backend:test
# (or: python -m pytest backend/tests/ -v)

# Re-seed demo database
npm run backend:seed
```
