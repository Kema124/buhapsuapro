from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

Base = declarative_base()

_engine = None
SessionLocal: Optional[sessionmaker] = None


def init_db(db_path: str | None = None):
    """Initialize DB engine.

    Priority:
      1) BUH_DB_URL env var (e.g. postgresql+psycopg://user:pass@host:5432/db)
      2) sqlite file path (db_path) (legacy mode)
    """
    global _engine, SessionLocal

    db_url = (os.getenv("BUH_DB_URL") or "").strip()
    if db_url:
        _engine = create_engine(db_url, echo=False, future=True)
    else:
        if not db_path:
            raise ValueError("db_path is required when BUH_DB_URL is not set")
        _engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)

    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError("База данных не инициализирована. Вызовите init_db() прежде.")
    return SessionLocal()
