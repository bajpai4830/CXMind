# Data Pipeline - ETL & Data Processing

## Overview
Current repository pipeline support is script-based and API-driven for local/demo workflows.

## Pipeline Components
1. **Seed Ingestion Script** - Generate synthetic interactions and POST to backend.
2. **Topic Training Utility** - Local script support for topic-model related workflows.

## Implemented Files

- `seed_data.py`
  - Generates synthetic examples and sends them to API endpoints.
- `train_topic.py`
  - Utility workflow for topic model training/retraining support.

## Not Implemented in This Repo

- No Spark/Airflow/Kafka orchestration pipeline.
- No production ETL scheduler under `data-pipeline/`.

## MVP: Seed Script
To generate synthetic interactions and POST them into the backend:
```powershell
cd data-pipeline
python seed_data.py --count 200
```

By default it targets `http://127.0.0.1:8000`.
