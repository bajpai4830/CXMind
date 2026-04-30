# Documentation

This folder contains implementation-facing documentation for the current CXMind codebase.

## Current Documents

- `ARCHITECTURE_MVP.md`
  - End-to-end system flow and currently implemented service boundaries.
- `ML_RUNTIME_PATH.md`
  - Canonical runtime ML inference path and auxiliary-module boundaries.
- `../PROJECT_STATE.md`
  - Code-verified implementation status, gaps, and prioritized next steps.

## Source of Truth

When documentation and code disagree, treat code as source of truth:

- Backend API routes: `backend/app/routers/`
- Data models: `backend/app/models.py`
- Frontend API integration: `frontend/src/api.ts`
- Runtime deployment config: `docker-compose.yml`

## Documentation Policy

- Avoid "coming soon" sections unless linked to a tracked issue.
- Mark planned work explicitly as **planned**.
- Keep architecture notes aligned with the current runtime stack (PostgreSQL + FastAPI + React).
