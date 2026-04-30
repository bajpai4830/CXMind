from __future__ import annotations

import os
import shutil
import unittest
import uuid

from fastapi.testclient import TestClient


class SecurityConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        base_tmpdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".tmp"))
        os.makedirs(base_tmpdir, exist_ok=True)
        self._tmpdir = os.path.join(base_tmpdir, f"security-config-{uuid.uuid4().hex}")
        os.makedirs(self._tmpdir, exist_ok=True)

        db_path = os.path.join(self._tmpdir, "test.db")
        os.environ["CXMIND_DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["CXMIND_CORS_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"

        from app.main import create_app  # noqa: WPS433 (test-only import)
        from app import db as db_module  # noqa: WPS433 (test-only import)

        self._db_module = db_module
        app = create_app()
        assert self._db_module.engine is not None
        self._db_module.Base.metadata.create_all(bind=self._db_module.engine)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        if self._db_module.engine is not None:
            self._db_module.engine.dispose()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_openapi_exposes_bearer_authorization(self) -> None:
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200, response.text)

        schema = response.json()
        security_schemes = schema["components"]["securitySchemes"]
        self.assertIn("HTTPBearer", security_schemes)
        self.assertEqual(security_schemes["HTTPBearer"]["type"], "http")
        self.assertEqual(security_schemes["HTTPBearer"]["scheme"], "bearer")

        me_operation = schema["paths"]["/api/v1/auth/me"]["get"]
        self.assertIn({"HTTPBearer": []}, me_operation.get("security", []))

    def test_cors_preflight_uses_explicit_allowed_origin(self) -> None:
        response = self.client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type,X-CSRF-Token",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:5173")
        self.assertEqual(response.headers.get("access-control-allow-credentials"), "true")

        allowed_headers = (response.headers.get("access-control-allow-headers") or "").lower()
        self.assertIn("authorization", allowed_headers)
        self.assertIn("content-type", allowed_headers)
        self.assertIn("x-csrf-token", allowed_headers)

    def test_security_headers_include_csp_and_xss_controls(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200, response.text)

        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("x-xss-protection"), "1; mode=block")

        csp = response.headers.get("content-security-policy") or ""
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)


if __name__ == "__main__":
    unittest.main()
