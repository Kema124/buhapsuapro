from __future__ import annotations

import re
from typing import Any

from sqlalchemy import or_, func
import database.db as db
from database.models import Contagent

_TOKEN_RE = re.compile(r"\s+", re.UNICODE)


def _tokens(query: str) -> list[str]:
    q = (query or "").strip()
    if not q:
        return []
    return [t for t in _TOKEN_RE.split(q) if t][:20]


# ------------------------
# LIST
# ------------------------

def get_all_contagents() -> list[Contagent]:
    session = db.get_session()
    try:
        return (
            session.query(Contagent)
            .filter(Contagent.is_deleted == False)
            .order_by(Contagent.name)
            .all()
        )
    finally:
        session.close()


def get_contagent_by_id(contagent_id: int) -> Contagent | None:
    session = db.get_session()
    try:
        return session.query(Contagent).filter(
            Contagent.id == contagent_id
        ).first()
    finally:
        session.close()


def get_deleted_contagent_by_id(contagent_id: int) -> Contagent | None:
    session = db.get_session()
    try:
        return session.query(Contagent).filter(
            Contagent.id == contagent_id,
            Contagent.is_deleted == True
        ).first()
    finally:
        session.close()


def get_deleted_contagents() -> list[Contagent]:
    session = db.get_session()
    try:
        return (
            session.query(Contagent)
            .filter(Contagent.is_deleted == True)
            .order_by(Contagent.name)
            .all()
        )
    finally:
        session.close()


# ------------------------
# CRUD
# ------------------------

def create_contagent(data: dict[str, Any]) -> int:
    session = db.get_session()
    try:
        obj = Contagent(**data)
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return int(obj.id)
    finally:
        session.close()


def update_contagent(contagent_id: int, data: dict[str, Any]) -> None:
    session = db.get_session()
    try:
        obj = session.query(Contagent).filter(
            Contagent.id == contagent_id
        ).first()

        if not obj:
            raise ValueError("Контрагент не найден")

        for k, v in data.items():
            setattr(obj, k, v)

        session.commit()
    finally:
        session.close()


# ------------------------
# ARCHIVE
# ------------------------

def soft_delete_contagent(contagent_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Contagent).filter(
            Contagent.id == contagent_id
        ).first()
        if not obj:
            raise ValueError("Контрагент не найден")
        obj.is_deleted = True
        session.commit()
    finally:
        session.close()


def restore_contagent(contagent_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Contagent).filter(
            Contagent.id == contagent_id
        ).first()
        if not obj:
            raise ValueError("Контрагент не найден")
        obj.is_deleted = False
        session.commit()
    finally:
        session.close()


def delete_contagent_forever(contagent_id: int) -> None:
    delete_contagents_forever([contagent_id])


def delete_contagents_forever(ids: list[int]) -> None:
    if not ids:
        return
    session = db.get_session()
    try:
        rows = session.query(Contagent).filter(
            Contagent.id.in_(ids)
        ).all()
        for r in rows:
            session.delete(r)
        session.commit()
    finally:
        session.close()


# ------------------------
# SEARCH
# ------------------------

def search_contagents(query: str) -> list[Contagent]:
    session = db.get_session()
    try:
        q = session.query(Contagent).filter(Contagent.is_deleted == False)

        for token in _tokens(query):
            low = token.lower()
            q = q.filter(
                or_(
                    func.lower(Contagent.name).like(f"%{low}%"),
                    Contagent.inn.like(f"%{low}%"),
                    Contagent.kpp.like(f"%{low}%"),
                )
            )

        return q.order_by(Contagent.name).all()
    finally:
        session.close()
