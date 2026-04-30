# PROJECT_STATE

## 1. Project Overview

CXMind is currently implemented as a containerized full-stack customer feedback analytics application. It ingests interaction text (single submit, bulk JSON, CSV upload), enriches records with NLP signals (sentiment, topic, emotion, intent), stores enriched data in a relational database, and exposes analytics/admin APIs consumed by React dashboards.

Real code-backed capabilities:
- Role-based authentication (analyst/admin) with JWT + cookie session support.
- Tenant-aware data access (`org_id` filtering in core analytics/interaction queries).
- Operational ingestion APIs and dashboard-connected analytics views.
- Admin workflows for user management, audit log viewing, and topic retrain trigger.
- Export and reporting primitives (CSV exports, system jobs table, scheduler scaffolding).

---

## 2. Tech Stack (Detected)

### Backend
- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy ORM + Alembic migrations
- SlowAPI rate limiting + custom middleware (CSRF/security headers)

### Frontend
- React 19 + TypeScript + Vite
- React Router
- Recharts (dashboard charts)
- Framer Motion (UI effects)

### Database
- PostgreSQL (active in `docker-compose.yml`)
- SQLite fallback supported via SQLAlchemy config path

### ML/AI
- VADER sentiment
- BERTopic/topic clustering path with fallback logic
- Optional Transformers/SentenceTransformers/spaCy/scikit-learn usage with graceful fallbacks in services
- Heuristic risk scoring + rule-based recommendation logic

### DevOps
- Docker + Docker Compose
- Nginx (frontend serving + API proxy)
- GitHub Actions CI workflow

---

## 3. Current Implementation Status

### ✅ Fully Implemented Features

- Auth flow: register, login, logout, current-user endpoint.
- Protected API access with role checks (admin endpoints restricted).
- Interaction ingestion via API (`/api/v1/interactions`, `/api/v1/interactions/log`).
- Bulk ingestion endpoints (`/api/v1/ingestion/bulk-json`, `/api/v1/ingestion/upload-csv`).
- NLP enrichment during ingestion (sentiment/topic/emotion/intent + journey + recommendations persisted).
- Dashboard analytics endpoints (summary, topics, sentiment trend).
- Frontend user dashboard connected to live API for ingest + metrics + charts + recent interactions.
- Frontend admin dashboard connected to live API for users, audit logs, jobs, retrain trigger.
- Containerized local deployment (`db`, `backend`, `frontend`) with DB health dependency.

### ⚠️ Partially Implemented Features

- Topic modeling has multiple paths (service + clustering utilities + standalone module), but not all modules are clearly in active runtime path.
- Scheduler/reporting exists in code but is environment-gated and not enabled by default.
- Customer segmentation/forecast utilities exist, but integration into primary API/dashboard path is limited.
- Multi-tenant isolation is mostly present, but feature-level consistency should be revalidated in all analytics/risk helper functions.

### ❌ Missing or Not Implemented

- `ml-models/` does not contain real model pipelines/artifacts despite documentation implying a broader ML stack.
- `data-pipeline/` does not implement Spark/Airflow/Kafka pipeline claims; only lightweight scripts are present.
- No evidence of real-time stream processing/websocket live updates.
- Documentation sections in `docs/` and `ml-models/` include placeholders ("Coming Soon", "To Be Defined"), not implemented systems.

---

## 4. Backend Analysis

### Key Routes and Purpose

- `GET /health`: service health check.
- `POST /api/v1/auth/register|login|logout`, `GET /api/v1/auth/me`: authentication/session lifecycle.
- `POST /api/v1/interactions`, `POST /api/v1/interactions/log`, `GET /api/v1/interactions`: core interaction ingest/list.
- `POST /api/v1/feedback/upload`: batch feedback ingest path.
- `POST /api/v1/ingestion/bulk-json`, `POST /api/v1/ingestion/upload-csv`: operational backfill/import.
- `GET /api/v1/analytics/summary|topics|sentiment-trend`: aggregated dashboard metrics.
- `GET /api/v1/analytics/cx-risk|recommendations`, export endpoints: insight/accessory analytics.
- `GET/POST/PATCH/DELETE /api/v1/admin/*`: user management, audit stream, retrain trigger, jobs.
- `GET /api/v1/journey`, `GET /api/v1/customer-journey/{customer_id}`: journey analytics.
- Compatibility aliases under `/api/*` are also wired.

### Authentication System Status

- Implemented and active in middleware/dependencies.
- Supports bearer token and cookie auth.
- Includes CSRF protections for cookie-authenticated mutating requests.
- Includes rate limiting and security header middleware.
- Role enforcement exists for admin-protected routes.

### Data Models and Relationships

Core ORM models are implemented for:
- Organizations, users, interactions.
- NLP result tables: sentiment, emotion, intent, topic.
- Journey events.
- Risk predictions and recommendations.
- Feedback records, reports, audit logs, and system jobs.

Migrations exist across multiple Alembic revisions, including org isolation changes.

### Analytics Logic (What Actually Works)

- Aggregate counts/averages by channel and sentiment label.
- Time-based sentiment trend aggregation.
- Topic frequency aggregation.
- Risk/recommendation retrieval APIs.
- CSV export route set.

These are implemented through SQLAlchemy query functions and registered API routes.

---

## 5. Frontend Analysis

### Pages and Components

- Implemented routes: `/login`, `/dashboard`, `/admin`.
- `ProtectedRoute` and auth context manage access/role gating.
- User dashboard includes:
  - Interaction submit form.
  - KPI cards.
  - Topic bar chart.
  - Sentiment trend chart.
  - Recent interactions table.
- Admin dashboard includes:
  - Platform KPIs.
  - User directory role/deactivate actions.
  - Audit stream.
  - Topic retrain trigger.
  - Sentiment distribution chart.

### Dashboard Capabilities

- Uses live API calls (not mocked) through `frontend/src/api.ts`.
- Handles partial-load failures (Promise settlement with error toasts).
- Includes auth-aware requests with cookies + CSRF header support.

### API Integration Status

- Strong integration for auth, interactions, summary analytics, topics, sentiment trend, admin users/logs/jobs/retrain.
- Endpoint mapping aligns with backend `/api/v1/*` routes.

### UI Completeness

- Core pages are functional for MVP demo.
- UI is polished but centered on core workflows; advanced drill-down and complex filtering are limited.

---

## 6. AI/ML Analysis

### Sentiment Analysis

- Implemented in backend service layer with scoring output (label + compound/confidence).
- Applied during ingestion/enrichment and persisted in both interaction fields and result table.
- Exposed indirectly via analytics endpoints used by dashboard.

### Topic Modeling

- Topic detection is integrated into ingestion enrichment.
- BERTopic-related/retraining support exists, with fallback approaches.
- Additional topic modules exist, but not all are clearly part of primary request path.

### Prediction Logic

- Risk scoring exists and is exposed via analytics endpoint.
- Forecasting and segmentation utilities are present as helper modules/scripts, but not fully demonstrated as central product flows.

---

## 7. End-to-End Flow Check

Flow target: **Input -> Processing -> Storage -> Analytics -> Dashboard**

### What Works

- **Input:** API and file-based ingestion endpoints are implemented.
- **Processing:** Ingestion triggers NLP enrichment + journey/recommendation logic.
- **Storage:** SQLAlchemy models and migrations persist interactions and derived outputs.
- **Analytics:** Aggregation/insight endpoints are available and query DB state.
- **Dashboard:** React pages fetch and render backend analytics/interactions.

### What Breaks / Is Fragile

- Optional ML dependencies can reduce output quality/features when unavailable (fallback behavior).
- Some ML modules are present but not clearly unified under one production inference strategy.
- Scheduler/report automation is scaffolded but not operational by default.

### What Is Missing

- Mature standalone `ml-models/` production pipeline/artifact lifecycle.
- End-to-end external ETL orchestration stack (Spark/Airflow/Kafka) referenced in docs but absent in implementation.

---

## 8. Key Gaps (MOST IMPORTANT)

1. **Documentation-to-code drift:** docs still describe planned or simplified architectures that do not match current code reality.
2. **ML integration inconsistency:** multiple topic/ML paths exist; operationally active path should be consolidated and documented.
3. **Pipeline claims exceed implementation:** advanced ETL/orchestration stack is not present; current data pipeline is mostly seed/training scripts.
4. **Operational hardening gaps:** scheduler/reporting and model lifecycle controls are not fully productionized.
5. **Risk area in tenant consistency:** org-level filtering is broadly used, but all downstream helpers should be audited for strict tenant safety.

---

## 9. Recommended Next Steps (Prioritized)

### 🔥 Critical (must fix)

- Align documentation with actual architecture and remove placeholder claims.
- Define one canonical ML inference path (especially topic modeling) and retire/label inactive modules.
- Add/complete tenant-safety audit across all analytics/risk queries and helper functions.
- Add integration tests for full ingest -> enrich -> analytics -> dashboard workflow.

### ⚡ Important (should improve)

- Enable and operationalize scheduler/report jobs with clear env/deployment defaults.
- Improve admin observability for model status, ingestion failures, and job failures.
- Strengthen validation/error handling for ingestion files and malformed payloads.

### ⭐ Optional (nice to have)

- Introduce real-time update channel for dashboard refresh.
- Add richer drill-down analytics (channel/topic/date/customer dimensions).
- Expand forecasting/segmentation outputs into visible product features.

---

## 10. Demo Readiness Assessment

**Can this project be demonstrated?**  
Yes. The current repository supports a credible MVP demo: authentication, interaction ingestion, enrichment, analytics APIs, and connected user/admin dashboards.

**What must be fixed before demo (minimum):**
- Verify environment setup has required NLP dependencies or confirm fallback behavior ahead of time.
- Seed representative data and verify dashboard sections populate consistently.
- Ensure admin credentials/roles are prepared and retrain action is safe in demo environment.

**What should be fixed soon after demo:**
- Consolidate ML architecture and clean documentation drift.
- Harden operational paths (scheduler, model lifecycle, tenant consistency checks).

