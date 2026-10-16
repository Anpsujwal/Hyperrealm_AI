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
│   ├── app/                # Application routes, models, auth, repositories, seed
│   ├── tests/              # Pytest test suite (39 automated tests)
│   └── requirements.txt    # Python dependencies
│
├── package.json            # Root workspace runner scripts
└── pyproject.toml          # Pytest configuration
```

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
