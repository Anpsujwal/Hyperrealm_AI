# ==============================================================================
# HYPERREALM - Multi-Stage Production Dockerfile
# Stage 1: Build React/Vite Frontend
# Stage 2: Python 3.12 Slim Runtime serving FastAPI + Frontend SPA Assets
# ==============================================================================

# ── Stage 1: Frontend Build ───────────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend dependency declarations
COPY frontend/package.json frontend/package-lock.json* ./

# Install frontend dependencies
RUN npm ci || npm install

# Copy frontend source code and configs
COPY frontend/ ./

# Build production bundle (outputs to /app/frontend/dist)
RUN npm run build

# ── Stage 2: Runtime Image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Python environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    PORT=8000 \
    HOST=0.0.0.0 \
    FRONTEND_DIST=/app/frontend/dist

WORKDIR /app

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application code
COPY backend/app ./backend/app

# Copy built frontend production bundle from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose HTTP port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start Uvicorn ASGI production server
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host ${HOST:-0.0.0.0} --port ${PORT:-8080} --workers 2"]
