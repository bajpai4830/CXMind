# CXMind

CXMind is an AI-powered Customer Experience analytics platform that turns raw customer interactions into operational insight. The platform combines FastAPI, PostgreSQL, React, BERTopic, and VADER sentiment analysis to help teams monitor sentiment, identify recurring issues, predict customer risk, and act on findings through role-based dashboards.

## Project Overview

CXMind is designed as a multi-tenant experience intelligence platform for support, operations, and customer success teams. It ingests feedback from multiple channels, normalizes it into a shared interaction model, enriches it with sentiment and topic signals, and exposes both API and dashboard workflows for analysts and admins.

Core outcomes:
- Centralize customer interactions from forms, APIs, and CSV uploads.
- Analyze sentiment and emerging themes automatically.
- Protect tenant data with authentication, RBAC, and organization isolation.
- Surface metrics and recent interactions in live dashboards.
- Support future automation such as risk forecasting and scheduled reporting.

## Feature List

- Sentiment analysis using VADER for fast interaction scoring.
- Topic modeling and topic retraining workflows using BERTopic.
- CX risk prediction and customer segmentation endpoints.
- Role-based authentication with admin and analyst access levels.
- Multi-tenant organization isolation for interactions and user access.
- Bulk CSV and JSON ingestion for operational backfills.
- Dashboard views for real-time KPIs, trends, and recent submissions.
- Audit logging, rate limiting, CSRF protection, CORS, and security headers.
- Automated report storage and scheduler hooks for recurring jobs.

## Architecture

### High-Level Flow

1. Frontend users authenticate through the FastAPI auth endpoints.
2. Customer interactions are submitted through API or CSV ingestion routes.
3. The backend enriches interactions with sentiment, topic, and downstream analytics signals.
4. PostgreSQL stores the normalized interaction, user, feedback, and reporting data.
5. React dashboards query live analytics endpoints for summaries, trends, and recent records.

### System Components

- `frontend/`
  React + TypeScript + Vite dashboard for analyst and admin workflows.
- `backend/`
  FastAPI application, SQLAlchemy models, auth, routers, and analytics services.
- `data-pipeline/`
  Demo and training scripts for seeding data and topic modeling.
- `docs/`
  Architecture notes and supporting documentation.
- `ml-models/`
  Model artifacts and experimentation assets.

### Backend Responsibilities

- Auth and session management with JWT-backed cookies and bearer tokens.
- Interaction ingestion from JSON APIs and CSV upload endpoints.
- Analytics endpoints for summary metrics, topics, sentiment trends, and risk views.
- Admin APIs for user management, audit visibility, and model retraining.

### Frontend Responsibilities

- Login and role-aware routing.
- Analyst dashboard for interaction submission and live results.
- Admin dashboard for user operations and platform monitoring.
- Shared API client with cookie auth, CSRF handling, and environment-aware backend resolution.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: React, TypeScript, Vite, Recharts, Framer Motion
- ML/NLP: BERTopic, VADER Sentiment, supporting analytics services
- DevOps: Docker, Docker Compose, Nginx

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── db.py
│   │   ├── models.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── features/
│   │   ├── pages/
│   │   └── styles/
│   ├── Dockerfile
│   └── package.json
├── data-pipeline/
├── docs/
├── ml-models/
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Docker Desktop or Docker Engine + Docker Compose
- Or for local development:
  Python 3.12+
  Node.js 22+
  PostgreSQL 16+

## Setup with Docker

### 1. Clone the repository

```powershell
git clone <repository-url>
cd mini_project
```

### 2. Start the full stack

```powershell
docker compose up --build
```

### 3. Access the services

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

### Docker Services

- `db`
  PostgreSQL 16 with persistent volume `cxmind_pg`
- `backend`
  FastAPI app with Alembic migration on startup
- `frontend`
  Vite build served by Nginx

## Local Development Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --port 8000
```

Recommended environment variables:

```env
CXMIND_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/cxmind
CXMIND_JWT_SECRET=change-me
CXMIND_AUTH_ENABLED=true
CXMIND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CXMIND_ADMIN_SECRET=supersecret
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend talks to the backend at `http://localhost:8000` in Vite dev and preview environments.

## Authentication and Roles

- `analyst`
  Can submit interactions, view dashboard metrics, and access analytics routes.
- `admin`
  Inherits analyst capabilities and can access admin endpoints such as user management and model retraining.

Auth flow:

1. `POST /api/v1/auth/register`
2. `POST /api/v1/auth/login`
3. `GET /api/v1/auth/me`
4. `POST /api/v1/auth/logout`

## API Documentation

Interactive API docs are available at:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Key Endpoints

#### Health

- `GET /health`

#### Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

#### Interactions

- `POST /api/v1/interactions`
- `POST /api/v1/interactions/log`
- `GET /api/v1/interactions`

#### Analytics

- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/topics`
- `GET /api/v1/analytics/sentiment-trend`
- `GET /api/v1/analytics/cx-risk`
- `GET /api/v1/analytics/recommendations`
- `GET /api/v1/analytics/export/interactions.csv`

#### Ingestion

- `POST /api/v1/ingestion/bulk-json`
- `POST /api/v1/ingestion/upload-csv`

#### Admin

- `GET /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{user_id}/role`
- `DELETE /api/v1/admin/users/{user_id}`
- `GET /api/v1/admin/audit-logs`
- `POST /api/v1/admin/retrain-topic-model`

## Data and Security Notes

- Authentication supports cookie-based sessions and bearer tokens.
- CSRF protection is enabled for cookie-authenticated write requests.
- CORS is explicitly configured for local frontend origins.
- Security headers are applied through middleware.
- Tenant-aware access uses `org_id` on protected interaction flows.

## Testing

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend checks:

```powershell
cd frontend
npm run typecheck
npm run build
```

## Screenshots

Add UI screenshots to `docs/screenshots/` and reference them here.

Suggested assets:

- `docs/screenshots/login.png`
- `docs/screenshots/analyst-dashboard.png`
- `docs/screenshots/admin-dashboard.png`
- `docs/screenshots/csv-ingestion.png`

Example section layout:

- Login screen
- Analyst dashboard with real interaction data
- Admin dashboard with user and audit controls
- CSV ingestion workflow

## Team Members

Current repository contributors:

- Ishika Khera
- bajpai4830

Update this section with full names, roles, and contact details before submission if your final project team differs from the current git history.

## Additional Documentation

- [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md)
- [docs/ARCHITECTURE_MVP.md](docs/ARCHITECTURE_MVP.md)
- [frontend/README.md](frontend/README.md)
- [backend/README.md](backend/README.md)

## License

See [LICENSE](LICENSE) for licensing details.
