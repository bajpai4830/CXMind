# CXMind MVP Architecture

This MVP implements an end-to-end thin slice of the CXMind specification:

1) Ingest customer feedback text from multiple channels  
2) Score sentiment (VADER)  
3) Persist interactions (SQLite)  
4) Serve aggregate analytics + recent events to a dashboard

## Components

### Backend (`backend/`)
- FastAPI app: `backend/app/main.py`
- Storage: SQLite via SQLAlchemy (tables auto-created on startup)
- Sentiment: VADER compound score in [-1, 1] + label thresholds

Endpoints:
- `GET /health`
- `POST /api/v1/interactions`
- `GET /api/v1/interactions?limit=...`
- `GET /api/v1/analytics/summary`

### Frontend (`frontend/`)
- Vite + React + TypeScript
- Proxy config routes `/api/*` and `/health` to `http://127.0.0.1:8000`
- Dashboard shows KPIs, channel volume chart, sentiment mix chart, and a recent interactions table

### Data Pipeline (`data-pipeline/`)
- `seed_data.py` generates synthetic interactions and posts them to the backend for demos

## Next (From Specification)
- Identity resolution + unified customer profiles
- Journey modeling across touchpoints and sequences
- Predictive CX risk scoring (churn / dissatisfaction)
- Explainable recommendations + action tracking loop

