# Backend - API Services & Business Logic

## Overview
FastAPI service for data ingestion and CX analytics (MVP).

## Services
- Data Ingestion APIs (MVP: interactions)
- Analytics Service (MVP: sentiment summaries)
- Journey Mapping / Alerts (future)

## Tech Stack (MVP)
- FastAPI + Uvicorn
- SQLite (via SQLAlchemy)
- VADER sentiment scoring

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
- `GET /api/v1/interactions?limit=50`
- `GET /api/v1/analytics/summary`
