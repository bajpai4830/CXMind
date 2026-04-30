"""Shared pytest fixtures for backend integration tests."""

from __future__ import annotations

import os
import shutil
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def auth_headers(token: str) -> dict[str, str]:
    """Builds an Authorization header for bearer-authenticated requests."""

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Creates an isolated application client backed by a local SQLite database."""

    tmp_root = backend_dir / ".tmp"
    tmp_root.mkdir(exist_ok=True)

    db_dir = tmp_root / f"pytest-{uuid.uuid4().hex}"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "test.db"

    os.environ["CXMIND_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["CXMIND_ADMIN_SECRET"] = "secret"
    os.environ["CXMIND_AUTH_ENABLED"] = "true"
    os.environ["CXMIND_CORS_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"

    from app.main import create_app
    from app import db as db_module

    app = create_app()
    assert db_module.engine is not None
    db_module.Base.metadata.create_all(bind=db_module.engine)

    with TestClient(app) as test_client:
        yield test_client

    if db_module.engine is not None:
        db_module.engine.dispose()

    shutil.rmtree(db_dir, ignore_errors=True)


@pytest.fixture
def db_session(client):
    """Provides a direct SQLAlchemy session for test-only data setup."""

    from app.db import SessionLocal

    assert SessionLocal is not None
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def register_user(client: TestClient):
    """Registers a user through the public authentication API."""

    def _register(email: str, password: str = "password123", *, is_admin: bool = False):
        payload = {"email": email, "password": password}
        if is_admin:
            payload["admin_secret"] = "secret"

        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    return _register


@pytest.fixture
def login_user(client: TestClient):
    """Logs in a user and returns the API response."""

    def _login(email: str, password: str = "password123", *, requested_role: str | None = None):
        payload: dict[str, str] = {"email": email, "password": password}
        if requested_role is not None:
            payload["requested_role"] = requested_role

        return client.post("/api/v1/auth/login", json=payload)

    return _login
