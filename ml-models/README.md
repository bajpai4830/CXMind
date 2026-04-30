# ML Models Directory

## Current Status

This directory is reserved for model artifacts and related assets.

At present, most production-facing NLP/ML logic is implemented in backend service modules under:

- `backend/app/services/sentiment_service.py`
- `backend/app/services/topic_service.py`
- `backend/app/services/emotion_service.py`
- `backend/app/services/intent_service.py`
- `backend/app/services/risk_service.py`

## What Is Implemented Today

- Sentiment, topic, emotion, and intent inference integrated into backend ingestion flow.
- Topic retrain trigger endpoint available through admin APIs.
- Heuristic risk scoring and recommendation generation in backend services.

## What Is Not Yet Implemented Here

- No complete standalone model training/serving pipeline in `ml-models/`.
- No committed, versioned model registry/artifact lifecycle in this directory.

## Usage Note

Treat backend service code as runtime source of truth until model lifecycle is formally moved into this directory.
