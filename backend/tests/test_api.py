from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_ok() -> None:
    app = create_app()
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_and_summary() -> None:
    app = create_app()
    client = TestClient(app)

    r = client.post(
        "/api/v1/interactions",
        json={"channel": "support_ticket", "text": "This is terrible, I'm upset."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["channel"] == "support_ticket"
    assert body["sentiment_label"] in {"negative", "neutral", "positive"}

    s = client.get("/api/v1/analytics/summary")
    assert s.status_code == 200
    summary = s.json()
    assert summary["total_interactions"] >= 1

