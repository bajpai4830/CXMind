from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_DEFAULT_DB_PATH = (Path(__file__).resolve().parents[1] / "cxmind.db").as_posix()
_DEFAULT_DB_URL = f"sqlite:///{_DEFAULT_DB_PATH}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CXMIND_", env_file=".env", extra="ignore")

    # Keep the default DB location stable regardless of the process working directory.
    database_url: str = _DEFAULT_DB_URL
    cors_origins: str = "http://localhost:5173"


settings = Settings()
