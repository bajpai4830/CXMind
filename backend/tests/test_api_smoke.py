from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class ApiSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        # Har test run ke liye alag SQLite DB use kar rahe hain, taaki local/dev DB touch na ho.
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = os.path.join(self._tmpdir.name, "test.db")
        os.environ["CXMIND_DATABASE_URL"] = f"sqlite:///{db_path}"

        # Import after env set so Settings picks up the DB URL.
        from app.main import create_app  # noqa: WPS433 (test-only import)

        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _register_and_login(self) -> str:
        r = self.client.post(
            "/api/v1/auth/register",
            json={"email": "admin@example.com", "password": "password123"},
        )
        self.assertEqual(r.status_code, 200, r.text)

        tok = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "password123"},
        )
        self.assertEqual(tok.status_code, 200, tok.text)
        return tok.json()["access_token"]

    def test_health_ok(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("status"), "ok")

    def test_auth_and_basic_flow(self) -> None:
        token = self._register_and_login()
        headers = {"Authorization": f"Bearer {token}"}

        me = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["email"], "admin@example.com")

        ing = self.client.post(
            "/api/v1/interactions",
            json={"channel": "support_ticket", "text": "This is terrible, I'm upset."},
            headers=headers,
        )
        self.assertEqual(ing.status_code, 200, ing.text)
        self.assertEqual(ing.json()["channel"], "support_ticket")

        s = self.client.get("/api/v1/analytics/summary", headers=headers)
        self.assertEqual(s.status_code, 200, s.text)
        self.assertGreaterEqual(int(s.json()["total_interactions"]), 1)


if __name__ == "__main__":
    unittest.main()

