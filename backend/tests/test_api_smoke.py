from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import auth_headers


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"


def test_auth_and_basic_flow(client: TestClient, register_user, login_user) -> None:
    register_user("admin@example.com")
    login_response = login_user("admin@example.com")
    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]
    headers = auth_headers(token)

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "admin@example.com"

    ingest = client.post(
        "/api/v1/interactions",
        json={"channel": "support_ticket", "text": "This is terrible, I'm upset."},
        headers=headers,
    )
    assert ingest.status_code == 200, ingest.text
    assert ingest.json()["channel"] == "support_ticket"

    summary = client.get("/api/v1/analytics/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    assert int(summary.json()["total_interactions"]) >= 1
