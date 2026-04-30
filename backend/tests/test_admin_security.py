from __future__ import annotations

from fastapi.testclient import TestClient

from app.models import User
from conftest import auth_headers


def _move_user_into_org(db_session, *, email: str, org_id: int) -> None:
    user = db_session.query(User).filter(User.email == email).one()
    user.org_id = org_id
    db_session.commit()


def test_login_with_wrong_role_returns_403(client: TestClient, register_user, login_user) -> None:
    register_user("analyst1@example.com")

    response = login_user("analyst1@example.com", requested_role="admin")
    assert response.status_code == 403
    assert "Unauthorized" in response.json()["detail"]


def test_analyst_cannot_access_admin_endpoints(client: TestClient, register_user, login_user) -> None:
    register_user("analyst2@example.com")
    login_response = login_user("analyst2@example.com")
    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]
    response = client.get("/api/v1/admin/users", headers=auth_headers(token))

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_self_demotion_returns_403(client: TestClient, register_user, login_user) -> None:
    register_user("admin1@example.com", is_admin=True)
    login_response = login_user("admin1@example.com", requested_role="admin")
    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=auth_headers(token))
    admin_id = me.json()["id"]

    response = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "analyst"},
        headers=auth_headers(token),
    )
    assert response.status_code == 403
    assert "Cannot demote your own admin account" in response.json()["detail"]


def test_deactivated_user_session_returns_401(
    client: TestClient,
    db_session,
    register_user,
    login_user,
) -> None:
    register_user("org-admin@example.com", is_admin=True)
    register_user("org-analyst@example.com")

    admin = db_session.query(User).filter(User.email == "org-admin@example.com").one()
    _move_user_into_org(db_session, email="org-analyst@example.com", org_id=admin.org_id)

    analyst_login = login_user("org-analyst@example.com")
    assert analyst_login.status_code == 200, analyst_login.text

    analyst_cookie = analyst_login.cookies.get("cxmind_token")
    assert analyst_cookie is not None

    analyst_me = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(analyst_login.json()["access_token"]),
    )
    analyst_id = analyst_me.json()["id"]

    admin_login = login_user("org-admin@example.com", requested_role="admin")
    assert admin_login.status_code == 200, admin_login.text

    deactivate = client.delete(
        f"/api/v1/admin/users/{analyst_id}",
        headers=auth_headers(admin_login.json()["access_token"]),
    )
    assert deactivate.status_code == 200, deactivate.text

    follow_up = client.get("/api/v1/auth/me", cookies={"cxmind_token": analyst_cookie})
    assert follow_up.status_code == 401
    assert follow_up.json()["detail"] in {"Invalid user", "Session revoked"}
