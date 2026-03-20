from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_DEFAULT_DB_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/cxmind"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CXMIND_", env_file=".env", extra="ignore")

    # Keep the default DB location stable regardless of the process working directory.
    database_url: str = _DEFAULT_DB_URL
    cors_origins: str = "http://localhost:5173"

    # Security
    auth_enabled: bool = True
    admin_secret: str = "supersecret"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    csrf_enabled: bool = True
    csrf_cookie_name: str = "cxmind_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120
    rate_limit_auth_per_minute: int = 20
    rate_limit_login: str = "10/15minutes"
    security_headers_enabled: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
