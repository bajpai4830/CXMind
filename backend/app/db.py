from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.settings import get_settings

Base = declarative_base()

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None
_engine_url: str | None = None


def _is_sqlite_memory_url(database_url: str) -> bool:
    url = (database_url or "").lower()
    return url in {"sqlite://", "sqlite:///:memory:"} or url.endswith(":memory:")


def init_engine(database_url: str) -> Engine:
    """
    (Re)initialize the SQLAlchemy engine + sessionmaker.

    This is intentionally dynamic so tests can swap `CXMIND_DATABASE_URL` between runs
    without needing a new Python process.
    """

    global engine, SessionLocal, _engine_url

    if engine is not None and _engine_url != database_url:
        engine.dispose()

    if engine is None or _engine_url != database_url:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        kwargs: dict[str, Any] = {"future": True, "connect_args": connect_args}

        if database_url.startswith("sqlite"):
            kwargs["poolclass"] = StaticPool if _is_sqlite_memory_url(database_url) else NullPool

        engine = create_engine(database_url, **kwargs)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        _engine_url = database_url

    assert engine is not None  # for type checkers
    return engine


def get_engine() -> Engine:
    settings = get_settings()
    return init_engine(settings.database_url)


def dispose_engine() -> None:
    global engine
    if engine is not None:
        engine.dispose()


def get_db() -> Generator[Session, None, None]:
    session_local = SessionLocal
    if session_local is None:
        session_local = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
        globals()["SessionLocal"] = session_local

    db = session_local()
    try:
        yield db
    finally:
        db.close()
