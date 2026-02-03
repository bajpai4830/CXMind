# Data Pipeline - ETL & Data Processing

## Overview
Data ingestion, transformation, and enrichment pipelines for multi-channel customer data.

## Pipeline Components
1. **Data Ingestion** - Connect to CRM, support systems, email, social media
2. **Data Normalization** - Standardize heterogeneous data formats
3. **Data Enrichment** - Add context and metadata
4. **Identity Resolution** - Unified customer profiles
5. **Quality Assurance** - Data validation and cleaning
6. **Aggregation** - Prepare data for ML models

## Tech Stack (To Be Defined)
- Apache Spark for large-scale processing
- Apache Airflow for orchestration
- Kafka for streaming data
- Python for custom processors

## MVP: Seed Script
To generate synthetic interactions and POST them into the backend:
```powershell
cd data-pipeline
python seed_data.py --count 200
```

By default it targets `http://127.0.0.1:8000`.
