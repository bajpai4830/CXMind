# ML Runtime Path

## Canonical Runtime Inference Flow

Production API ingestion uses this path:

1. Request arrives at interaction/ingestion router (`backend/app/routers/`).
2. `processing_service.enrich_interaction()` runs enrichment.
3. Runtime services execute:
   - `sentiment_service.score`
   - `topic_service.detect_topic`
   - `emotion_service.detect`
   - `intent_service.classify`
4. Enriched records are persisted in interaction + result tables.

## Topic Modeling Canonical Path

- Primary runtime entrypoint: `backend/app/services/topic_service.py`
- Topic model integration/fallback behavior: `backend/app/topic_clustering.py`
- Keyword-first deterministic mapping: `backend/app/topic_keywords.py`

## Non-Canonical / Auxiliary Modules

- `backend/app/topic_model.py`
  - Experimental embedding-based helper, not wired as the primary API runtime path.
- `backend/app/customer_segmentation.py`
  - Optional analytics utility endpoint dependency, not core ingestion enrichment.
- `backend/app/cx_forecast.py`
  - Heuristic forecasting endpoint support, separate from ingest-time enrichment.

## Operational Guidance

- Treat service-layer modules under `backend/app/services/` as source of truth for runtime behavior.
- Keep auxiliary modules clearly labeled as experimental or optional until fully integrated.
