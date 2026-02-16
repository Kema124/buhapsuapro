from __future__ import annotations

import json
import os
from typing import Any, Mapping

from config import DATA_DIR
from database.db import Base, init_db, get_session
from database.models import Organization

REGISTRY_PATH = os.path.join(DATA_DIR, "registry.json")


# ---------- registry ----------
def load_registry() -> dict[str, str]:
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # гарантируем тип словаря
    return dict(data)


def save_registry(data: Mapping[str, str]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(dict(data), f, ensure_ascii=False, indent=2)


# ---------- database creation ----------
def create_new_database(org_name: str) -> str:
    folder_name = org_name.replace(" ", "_")
    db_dir = os.path.join(DATA_DIR, folder_name)
    db_path = os.path.join(db_dir, "accounting.db")

    os.makedirs(db_dir, exist_ok=True)

    engine = init_db(db_path)
    Base.metadata.create_all(bind=engine)

    # сохраняем абсолютный путь
    registry = load_registry()
    registry[org_name] = os.path.abspath(db_path)
    save_registry(registry)

    return db_path


# ---------- organization CRUD ----------
def get_organization() -> Organization | None:
    session = get_session()
    try:
        return session.query(Organization).first()
    finally:
        session.close()


def create_organization(data: Mapping[str, Any]) -> Organization:
    session = get_session()
    try:
        exists = session.query(Organization).first()
        if exists is not None:
            raise ValueError("Организация уже существует")

        org = Organization(**dict(data))
        session.add(org)
        session.commit()
        session.refresh(org)
        return org
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_organization(data: Mapping[str, Any]) -> Organization:
    session = get_session()
    try:
        org: Organization | None = session.query(Organization).first()
        if org is None:
            raise ValueError("Организация не найдена")

        for key, value in dict(data).items():
            setattr(org, key, value)

        session.commit()
        session.refresh(org)
        return org
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
