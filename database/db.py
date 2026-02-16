from __future__ import annotations

from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

Base = declarative_base()

_engine = None
SessionLocal: Optional[sessionmaker] = None


def init_db(db_path: str):
    global _engine, SessionLocal
    _engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError("База данных не инициализирована. Вызовите init_db() прежде.")
    return SessionLocal()
