# CXMind MVP Architecture

This MVP implements an end-to-end thin slice of the CXMind platform:

1) Ingest customer feedback text from multiple channels  
2) Score sentiment (VADER)  
3) Persist interactions and enrichment outputs (PostgreSQL in docker-compose, SQLite fallback supported)  
4) Serve aggregate analytics + recent events to a dashboard

## Components

### Backend (`backend/`)
- FastAPI app: `backend/app/main.py`
- Storage: SQLAlchemy + Alembic migrations, Postgres-first in container setup
- Enrichment: sentiment, topic, emotion, and intent services executed at ingestion time
- Security: JWT auth, role checks, CSRF middleware, rate limiting, security headers

Endpoints:
- `GET /health`
- `POST /api/v1/interactions`
- `GET /api/v1/interactions?limit=...`
- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/topics`
- `GET /api/v1/analytics/sentiment-trend`
- `POST /api/v1/ingestion/bulk-json`
- `POST /api/v1/ingestion/upload-csv`
- `GET /api/v1/admin/users`

### Frontend (`frontend/`)
- Vite + React + TypeScript
- Authenticated routes for user and admin dashboards
- Dashboard shows KPIs, topic/sentiment visualizations, and recent interactions
- Frontend API client handles credentials + CSRF for write operations

### Data Pipeline (`data-pipeline/`)
- `seed_data.py` generates synthetic interactions and posts to backend APIs
- `train_topic.py` provides topic-training utility scripts used by developers/admin workflows

### ML Assets (`ml-models/`)
- Intended location for model artifacts.
- Current runtime logic mostly lives in backend services; this directory is not yet a complete standalone ML pipeline.

## Known Gaps
- Docs and implementation can drift; verify against `PROJECT_STATE.md` for latest code-verified status.
- Scheduler/reporting is present but disabled unless explicitly enabled via environment configuration.

