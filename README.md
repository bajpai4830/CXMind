# CXMind

AI-powered Customer Experience (CX) Analytics Platform that unifies customer interactions across channels, analyzes sentiment and behavior using AI, and provides actionable insights to improve customer journeys.

## Features

- **Multimodal Sentiment Analysis**: Analyze sentiment across text interactions using NLP models
- **Topic Modeling**: Automatic categorization of feedback and issues
- **Customer Journey Mapping**: Identify patterns across entire customer journeys
- **Predictive Analytics**: Forecast CX outcomes like churn and dissatisfaction
- **Real-time Dashboards**: Interactive visualizations for KPIs, trends, and journey maps
- **Data Ingestion**: APIs for integrating CRM, support tickets, emails, and social media
- **Explainable Insights**: Link CX metrics to business outcomes with clear explanations

## Prerequisites

- Python 3.8+
- Node.js 16+ (for React frontend, optional)
- PostgreSQL 12+ (database)
- Git

## Installation

### 1) Clone the Repository
```powershell
git clone <repository-url>
cd CXMind
```

### 2) Set Up Environment Variables
Copy the example environment file and configure it:
```powershell
cp .env.example .env
```
Edit `.env` with your PostgreSQL credentials:
```
CXMIND_DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/cxmind
```

### 3) Install Python Dependencies
Create a virtual environment and install dependencies:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
This installs:
- FastAPI, Uvicorn (web framework)
- SQLAlchemy (ORM)
- Pydantic (data validation)
- VADER Sentiment (sentiment analysis)
- BERTopic (topic modeling)
- psycopg2 (PostgreSQL driver)
- Streamlit (dashboard)
- pytest, httpx (testing)
- Other dependencies from backend/requirements.txt

### 4) Set Up PostgreSQL Database
Ensure PostgreSQL is running and create the database:
```sql
CREATE DATABASE cxmind;
```
The application will automatically create tables on startup.

### 5) Install Frontend Dependencies (Optional, for React Dashboard)
```powershell
cd frontend
npm install
```
This installs:
- React, React DOM
- Recharts (charts library)
- Vite (build tool)
- TypeScript, ESLint (development)

## Repo Layout

- `backend/` - FastAPI API with PostgreSQL persistence
  - `app/` - Main application code
    - `routers/` - API endpoints (analytics, interactions, journey, admin, health)
    - ML modules: sentiment analysis, topic modeling, clustering, etc.
  - `tests/` - API tests using pytest
  - `ml-models/` - Trained ML models (e.g., topic model)
- `frontend/` - React + TypeScript dashboard with Vite (optional)
  - Interactive charts for sentiment, topics, and customer journeys
- `data-pipeline/` - ETL scripts for data processing
  - `seed_data.py` - Generate sample customer interactions
  - `train_topic.py` - Train topic modeling on interaction data
- `ml-models/` - Model experiments and training scripts
- `deployment/` - Deployment configurations and IaC (future)
- `docs/` - Documentation and architecture specs
- `dashboard.py` - Streamlit dashboard for analytics visualization
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Quickstart

### 1) Start Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### 2) Seed Sample Data
In a new terminal:
```powershell
cd data-pipeline
.\.venv\Scripts\Activate.ps1
python seed_data.py --count 200
```

### 3) Train Topic Model
After seeding data:
```powershell
cd data-pipeline
.\.venv\Scripts\Activate.ps1
python train_topic.py
```

### 4) Start Streamlit Dashboard
In a new terminal:
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run dashboard.py
```
Open at `http://localhost:8501`

### 5) React Frontend Dashboard (Alternative)
In a new terminal:
```powershell
cd frontend
npm run dev
```
Open at `http://localhost:5173`

## Testing

Run backend tests:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest tests/
```

## Deployment

See `deployment/README.md` for deployment instructions (future implementation).

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API docs.

## Docs

- `PROJECT_SPECIFICATION.md` - Detailed product specification and architecture
- `docs/ARCHITECTURE_MVP.md` - MVP architecture details
- `docs/README.md` - Additional documentation

## Contributing

See `CONTRIBUTING.md` for contribution guidelines.

## License

See `LICENSE` for licensing information.
