import os
import tempfile
import pytest
from unittest.mock import patch
import threading
import time
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client():
    tmpdir = tempfile.TemporaryDirectory()
    os.environ["CXMIND_DATABASE_URL"] = f"sqlite:///{os.path.join(tmpdir.name, 'test.db')}"
    os.environ["CXMIND_ADMIN_SECRET"] = "secret"
    os.environ["CXMIND_AUTH_ENABLED"] = "true"
    
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    from app.main import create_app
    app = create_app()
    
    from app.db import Base, engine
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client

    engine.dispose()
    
    try:
        tmpdir.cleanup()
    except Exception:
        pass

def test_role_mismatch_returns_403(client: TestClient):
    client.post("/api/v1/auth/register", json={"email": "analyst1@example.com", "password": "password123"})
    res = client.post("/api/v1/auth/login", json={"email": "analyst1@example.com", "password": "password123", "requested_role": "admin"})
    assert res.status_code == 403
    assert "Unauthorized" in res.json()["detail"]

def test_self_demotion_returns_403(client: TestClient):
    client.post("/api/v1/auth/register", json={"email": "admin1@example.com", "password": "password123", "admin_secret": "secret"})
    res = client.post("/api/v1/auth/login", json={"email": "admin1@example.com", "password": "password123", "requested_role": "admin"})
    token = res.json()["access_token"]
    
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    admin_id = me["id"]
    
    demote = client.patch(f"/api/v1/admin/users/{admin_id}/role", json={"role": "analyst"}, headers={"Authorization": f"Bearer {token}"})
    assert demote.status_code == 403
    assert "Cannot demote your own admin account" in demote.json()["detail"]

def test_deactivated_user_cookie_returns_401(client: TestClient):
    client.post("/api/v1/auth/register", json={"email": "analyst2@example.com", "password": "password123"})
    res = client.post("/api/v1/auth/login", json={"email": "analyst2@example.com", "password": "password123"})
    analyst_token = res.json()["access_token"]
    
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {analyst_token}"}).json()
    analyst_id = me["id"]
    
    res_admin = client.post("/api/v1/auth/login", json={"email": "admin1@example.com", "password": "password123"})
    admin_token = res_admin.json()["access_token"]
    
    deact = client.delete(f"/api/v1/admin/users/{analyst_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert deact.status_code == 200
    
    from app.main import create_app
    client2 = TestClient(create_app(), cookies={"cxmind_token": analyst_token})
    subsequent = client2.get("/api/v1/auth/me")
    
    assert subsequent.status_code == 401
    assert "Invalid user" in subsequent.json()["detail"] or "Session revoked" in subsequent.json()["detail"]

@patch("app.routers.admin.train_topic_model")
def test_double_fire_retrain_returns_400(mock_train, client: TestClient):
    res_admin = client.post("/api/v1/auth/login", json={"email": "admin1@example.com", "password": "password123"})
    admin_token = res_admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Needs at least 5 texts to bypass 'not enough data' clause
    for i in range(5):
        client.post("/api/v1/interactions", json={"channel": "web", "text": f"test data {i}"}, headers=headers)
        
    retrain1 = client.post("/api/v1/admin/retrain-topic-model", headers=headers)
    assert retrain1.status_code == 200
    
    retrain2 = client.post("/api/v1/admin/retrain-topic-model", headers=headers)
    # The second run must fail because of the cooldown tracking (or atomic lock)
    assert retrain2.status_code in [400, 429]
    assert "Cooldown active" in retrain2.json()["detail"] or "ob is already" in retrain2.json()["detail"]
