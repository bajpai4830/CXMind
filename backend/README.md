# Backend - API Services & Business Logic

## Overview
FastAPI service for data ingestion and CX analytics.

## Services
- Data ingestion APIs (interactions + feedback batch uploads)
- NLP enrichment (sentiment, topic, emotion, intent)
- Journey mapping (stage classification + friction analytics)
- CX risk scoring (heuristic baseline)
- Recommendations (rule-based baseline)

## Tech Stack
- FastAPI + Uvicorn
- SQLAlchemy (SQLite by default; Postgres via `CXMIND_DATABASE_URL`)
- Optional Transformers-based NLP with offline-safe fallbacks

## Quickstart
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API
- `GET /health`
- `POST /api/v1/interactions` `{ customer_id?, channel, text }`
- `POST /api/v1/interactions/log` `{ customer_id?, channel, message|text, timestamp?, session_id?, metadata? }`
- `GET /api/v1/interactions?limit=50`
- `POST /api/v1/feedback/upload` `{ items: [...] }`
- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/sentiment-trend`
- `GET /api/v1/analytics/topics`
- `GET /api/v1/analytics/cx-risk`
- `GET /api/v1/analytics/recommendations`
- `GET /api/v1/journey`

Compat endpoints (for the spec):
- `POST /api/interactions/log`
- `POST /api/feedback/upload`
- `GET /api/analytics/summary`
- `GET /api/journey`
