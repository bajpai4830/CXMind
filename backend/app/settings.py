from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


_DEFAULT_DB_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/cxmind"
_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "https://cx-mind.vercel.app",
)
_DEFAULT_CORS_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
_DEFAULT_CORS_HEADERS = ("Authorization", "Content-Type", "X-CSRF-Token")
_DEFAULT_EXPOSE_HEADERS = (
    "Content-Security-Policy",
    "Permissions-Policy",
    "Referrer-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CXMIND_", env_file=".env", extra="ignore")

    # Keep the default DB location stable regardless of the process working directory.
    database_url: str = _DEFAULT_DB_URL
    cors_origins: str = ",".join(_DEFAULT_CORS_ORIGINS)
    cors_allow_credentials: bool = True
    cors_allow_methods: str = ",".join(_DEFAULT_CORS_METHODS)
    cors_allow_headers: str = ",".join(_DEFAULT_CORS_HEADERS)
    cors_expose_headers: str = ",".join(_DEFAULT_EXPOSE_HEADERS)
    cors_max_age: int = 600

    # Security
    auth_enabled: bool = True
    admin_secret: str = "supersecret"
    auth_cookie_name: str = "cxmind_token"
    cookie_secure: bool = True
    cookie_samesite: str = "none"

    csrf_enabled: bool = False
    csrf_cookie_name: str = "cxmind_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 120
    rate_limit_auth_per_minute: int = 20
    rate_limit_login: str = "100/minute"
    security_headers_enabled: bool = True
    security_content_type_options: str = "nosniff"
    security_frame_options: str = "DENY"
    security_referrer_policy: str = "strict-origin-when-cross-origin"
    security_permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    security_content_security_policy: str = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "connect-src 'self'"
    )
    security_xss_protection: str = "1; mode=block"
    security_cross_origin_opener_policy: str = "same-origin"
    security_cross_origin_resource_policy: str = "same-origin"
    security_hsts_enabled: bool = False
    security_hsts_value: str = "max-age=63072000; includeSubDomains"

    @staticmethod
    def _csv_to_list(raw_value: str) -> list[str]:
        return [item.strip() for item in raw_value.split(",") if item.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return self._csv_to_list(self.cors_origins) or list(_DEFAULT_CORS_ORIGINS)

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return self._csv_to_list(self.cors_allow_methods) or list(_DEFAULT_CORS_METHODS)

    @property
    def cors_allow_headers_list(self) -> list[str]:
        return self._csv_to_list(self.cors_allow_headers) or list(_DEFAULT_CORS_HEADERS)

    @property
    def cors_expose_headers_list(self) -> list[str]:
        return self._csv_to_list(self.cors_expose_headers) or list(_DEFAULT_EXPOSE_HEADERS)

    @property
    def security_headers(self) -> dict[str, str]:
        headers = {
            "Content-Security-Policy": self.security_content_security_policy,
            "Cross-Origin-Opener-Policy": self.security_cross_origin_opener_policy,
            "Cross-Origin-Resource-Policy": self.security_cross_origin_resource_policy,
            "Permissions-Policy": self.security_permissions_policy,
            "Referrer-Policy": self.security_referrer_policy,
            "X-Content-Type-Options": self.security_content_type_options,
            "X-Frame-Options": self.security_frame_options,
            "X-XSS-Protection": self.security_xss_protection,
        }
        if self.security_hsts_enabled:
            headers["Strict-Transport-Security"] = self.security_hsts_value
        return headers


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
