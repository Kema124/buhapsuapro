from __future__ import annotations

import re
from typing import Any

from sqlalchemy import or_, func

import database.db as db
from database.models import Tax

_TOKEN_RE = re.compile(r"\s+", re.UNICODE)


def _tokens(query: str) -> list[str]:
    q = (query or "").strip()
    if not q:
        return []
    return [t for t in _TOKEN_RE.split(q) if t][:20]


def get_all_taxes() -> list[Tax]:
    session = db.get_session()
    try:
        return (
            session.query(Tax)
            .filter(Tax.is_deleted == False)
            .order_by(Tax.name)
            .all()
        )
    finally:
        session.close()


def get_tax_by_id(tax_id: int) -> Tax | None:
    session = db.get_session()
    try:
        return session.query(Tax).filter(Tax.id == tax_id).first()
    finally:
        session.close()


def get_deleted_taxes() -> list[Tax]:
    session = db.get_session()
    try:
        return (
            session.query(Tax)
            .filter(Tax.is_deleted == True)
            .order_by(Tax.name)
            .all()
        )
    finally:
        session.close()


def create_tax(data: dict[str, Any]) -> int:
    session = db.get_session()
    try:
        obj = Tax(**data)
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return int(obj.id)
    finally:
        session.close()


def update_tax(tax_id: int, data: dict[str, Any]) -> None:
    session = db.get_session()
    try:
        obj = session.query(Tax).filter(Tax.id == tax_id, Tax.is_deleted == False).first()
        if not obj:
            raise ValueError("Налог не найден")
        for k, v in data.items():
            setattr(obj, k, v)
        session.commit()
    finally:
        session.close()


def soft_delete_tax(tax_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Tax).filter(Tax.id == tax_id).first()
        if not obj:
            raise ValueError("Налог не найден")
        obj.is_deleted = True
        session.commit()
    finally:
        session.close()


def restore_tax(tax_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Tax).filter(Tax.id == tax_id).first()
        if not obj:
            raise ValueError("Налог не найден")
        obj.is_deleted = False
        session.commit()
    finally:
        session.close()


def delete_taxes_forever(tax_ids: list[int]) -> None:
    if not tax_ids:
        return
    session = db.get_session()
    try:
        session.query(Tax).filter(Tax.id.in_(tax_ids)).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def search_taxes(query: str) -> list[Tax]:
    session = db.get_session()
    try:
        q = session.query(Tax).filter(Tax.is_deleted == False)
        for token in _tokens(query):
            low = token.lower()
            q = q.filter(or_(
                func.lower(Tax.name).like(f"%{low}%"),
                func.lower(func.coalesce(Tax.kbk, "")).like(f"%{low}%"),
                func.lower(func.coalesce(Tax.rate, "")).like(f"%{low}%"),
                func.lower(func.coalesce(Tax.tax_type, "")).like(f"%{low}%"),
            ))
        return q.order_by(Tax.name).all()
    finally:
        session.close()


def filter_taxes(filters: dict[str, Any]) -> list[Tax]:
    """Фильтр (как в 1С). Поддерживает: name, kbk."""
    session = db.get_session()
    try:
        q = session.query(Tax).filter(Tax.is_deleted == False)
        if filters.get("name"):
            low = str(filters["name"]).lower()
            q = q.filter(func.lower(Tax.name).like(f"%{low}%"))
        if filters.get("kbk"):
            q = q.filter(func.coalesce(Tax.kbk, "").like(f"%{filters['kbk']}%"))
        return q.order_by(Tax.name).all()
    finally:
        session.close()
