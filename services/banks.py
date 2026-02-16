from __future__ import annotations

import re
from typing import Any

from sqlalchemy import or_, func

import database.db as db
from database.models import Bank

_TOKEN_RE = re.compile(r"\s+", re.UNICODE)


def _tokens(query: str) -> list[str]:
    q = (query or "").strip()
    if not q:
        return []
    return [t for t in _TOKEN_RE.split(q) if t][:20]


def get_all_banks() -> list[Bank]:
    session = db.get_session()
    try:
        return (
            session.query(Bank)
            .filter(Bank.is_deleted == False)
            .order_by(Bank.name)
            .all()
        )
    finally:
        session.close()


def get_bank_by_id(bank_id: int) -> Bank | None:
    session = db.get_session()
    try:
        return session.query(Bank).filter(Bank.id == bank_id).first()
    finally:
        session.close()


def get_deleted_banks() -> list[Bank]:
    session = db.get_session()
    try:
        return (
            session.query(Bank)
            .filter(Bank.is_deleted == True)
            .order_by(Bank.name)
            .all()
        )
    finally:
        session.close()


def create_bank(data: dict[str, Any]) -> int:
    session = db.get_session()
    try:
        obj = Bank(**data)
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return int(obj.id)
    finally:
        session.close()


def update_bank(bank_id: int, data: dict[str, Any]) -> None:
    session = db.get_session()
    try:
        obj = session.query(Bank).filter(Bank.id == bank_id, Bank.is_deleted == False).first()
        if not obj:
            raise ValueError("Банк не найден")
        for k, v in data.items():
            setattr(obj, k, v)
        session.commit()
    finally:
        session.close()


def soft_delete_bank(bank_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Bank).filter(Bank.id == bank_id).first()
        if not obj:
            raise ValueError("Банк не найден")
        obj.is_deleted = True
        session.commit()
    finally:
        session.close()


def restore_bank(bank_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Bank).filter(Bank.id == bank_id).first()
        if not obj:
            raise ValueError("Банк не найден")
        obj.is_deleted = False
        session.commit()
    finally:
        session.close()


def delete_banks_forever(bank_ids: list[int]) -> None:
    if not bank_ids:
        return
    session = db.get_session()
    try:
        session.query(Bank).filter(Bank.id.in_(bank_ids)).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def search_banks(query: str) -> list[Bank]:
    session = db.get_session()
    try:
        q = session.query(Bank).filter(Bank.is_deleted == False)
        for token in _tokens(query):
            low = token.lower()
            q = q.filter(or_(
                func.lower(Bank.name).like(f"%{low}%"),
                func.lower(func.coalesce(Bank.bik, "")).like(f"%{low}%"),
                func.lower(func.coalesce(Bank.swift, "")).like(f"%{low}%"),
                func.lower(func.coalesce(Bank.corr_account, "")).like(f"%{low}%"),
                func.lower(func.coalesce(Bank.address, "")).like(f"%{low}%"),
            ))
        return q.order_by(Bank.name).all()
    finally:
        session.close()
