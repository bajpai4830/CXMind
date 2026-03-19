from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Use a dev DB by default to avoid committing a stale schema in-repo.
_DEFAULT_DB_PATH = (Path(__file__).resolve().parents[1] / "cxmind_dev.db").as_posix()
_DEFAULT_DB_URL = f"sqlite:///{_DEFAULT_DB_PATH}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CXMIND_", env_file=".env", extra="ignore")

    # Keep the default DB location stable regardless of the process working directory.
    database_url: str = _DEFAULT_DB_URL
    cors_origins: str = "http://localhost:5173"

    # Security
    auth_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120
    rate_limit_auth_per_minute: int = 20
    security_headers_enabled: bool = True


settings = Settings()
