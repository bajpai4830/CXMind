from __future__ import annotations

import io

from fastapi.testclient import TestClient

from conftest import auth_headers
from app.models import Interaction
from app.services import risk_service


def test_user_cannot_see_other_org_interactions(client: TestClient, register_user, login_user) -> None:
    register_user("usera@example.com")
    register_user("userb@example.com")

    user_a_login = login_user("usera@example.com")
    user_b_login = login_user("userb@example.com")
    assert user_a_login.status_code == 200, user_a_login.text
    assert user_b_login.status_code == 200, user_b_login.text

    user_a_headers = auth_headers(user_a_login.json()["access_token"])
    user_b_headers = auth_headers(user_b_login.json()["access_token"])

    create_a = client.post(
        "/api/v1/interactions",
        json={"channel": "email", "text": "User A interaction"},
        headers=user_a_headers,
    )
    create_b = client.post(
        "/api/v1/interactions",
        json={"channel": "email", "text": "User B interaction"},
        headers=user_b_headers,
    )
    assert create_a.status_code == 200, create_a.text
    assert create_b.status_code == 200, create_b.text

    user_a_rows = client.get("/api/v1/interactions?limit=10", headers=user_a_headers)
    user_b_rows = client.get("/api/v1/interactions?limit=10", headers=user_b_headers)
    assert user_a_rows.status_code == 200, user_a_rows.text
    assert user_b_rows.status_code == 200, user_b_rows.text

    assert [row["text"] for row in user_a_rows.json()] == ["User A interaction"]
    assert [row["text"] for row in user_b_rows.json()] == ["User B interaction"]


def test_csv_upload_ingests_correctly(client: TestClient, register_user, login_user) -> None:
    register_user("csv@example.com")
    login_response = login_user("csv@example.com")
    assert login_response.status_code == 200, login_response.text

    headers = auth_headers(login_response.json()["access_token"])
    csv_payload = io.BytesIO(
        b"customer_id,channel,text\ncust-100,support_ticket,The delivery was delayed.\ncust-101,email,Great support experience.\n"
    )

    response = client.post(
        "/api/v1/ingestion/upload-csv",
        headers=headers,
        files={"file": ("interactions.csv", csv_payload, "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["inserted"] == 2

    interactions = client.get("/api/v1/interactions?limit=10", headers=headers)
    assert interactions.status_code == 200, interactions.text

    texts = [row["text"] for row in interactions.json()]
    assert texts == ["Great support experience.", "The delivery was delayed."]


def test_ingest_enrich_and_analytics_flow(client: TestClient, register_user, login_user) -> None:
    register_user("flow@example.com")
    login_response = login_user("flow@example.com")
    assert login_response.status_code == 200, login_response.text

    headers = auth_headers(login_response.json()["access_token"])

    ingest = client.post(
        "/api/v1/interactions",
        json={"customer_id": "cust-flow-1", "channel": "support_ticket", "text": "I am upset about delayed delivery."},
        headers=headers,
    )
    assert ingest.status_code == 200, ingest.text
    payload = ingest.json()
    assert payload["customer_id"] == "cust-flow-1"
    assert payload["topic"] is not None
    assert payload["sentiment_label"] in {"positive", "neutral", "negative"}

    interactions = client.get("/api/v1/interactions?limit=10", headers=headers)
    assert interactions.status_code == 200, interactions.text
    rows = interactions.json()
    assert len(rows) >= 1
    assert rows[0]["text"] == "I am upset about delayed delivery."

    summary = client.get("/api/v1/analytics/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    assert int(summary.json()["total_interactions"]) >= 1

    topics = client.get("/api/v1/analytics/topics", headers=headers)
    assert topics.status_code == 200, topics.text
    assert isinstance(topics.json(), list)
    assert len(topics.json()) >= 1


def test_risk_feature_computation_is_org_scoped(db_session) -> None:
    db_session.add_all(
        [
            Interaction(
                org_id=1,
                customer_id="cust-shared-1",
                channel="email",
                text="Org A negative signal",
                sentiment_label="negative",
                sentiment_compound=-0.7,
                topic="payment_problem",
            ),
            Interaction(
                org_id=2,
                customer_id="cust-shared-1",
                channel="email",
                text="Org B positive signal",
                sentiment_label="positive",
                sentiment_compound=0.8,
                topic="general_feedback",
            ),
        ]
    )
    db_session.commit()

    org_a = risk_service.compute_customer_features(db_session, "cust-shared-1", org_id=1)
    org_b = risk_service.compute_customer_features(db_session, "cust-shared-1", org_id=2)
    global_unscoped = risk_service.compute_customer_features(db_session, "cust-shared-1")

    assert int(org_a["total_interactions"]) == 1
    assert int(org_b["total_interactions"]) == 1
    assert int(global_unscoped["total_interactions"]) == 2
