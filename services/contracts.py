from __future__ import annotations

import re
from typing import Any

from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

import database.db as db
from database.models import Contract, Contagent


# --- статусы договора (единый источник) ---
STATUS_DRAFT = "draft"
STATUS_ACTIVE = "active"
STATUS_CLOSED = "closed"

CONTRACT_STATUSES = (STATUS_DRAFT, STATUS_ACTIVE, STATUS_CLOSED)

STATUS_TITLES = {
    STATUS_DRAFT: "Черновик",
    STATUS_ACTIVE: "Активен",
    STATUS_CLOSED: "Закрыт",
}

_TOKEN_RE = re.compile(r"\s+", re.UNICODE)


def _tokens(query: str) -> list[str]:
    q = (query or "").strip()
    if not q:
        return []
    return [t for t in _TOKEN_RE.split(q) if t][:20]


# =========================
# LIST
# =========================

def get_all_contracts() -> list[Contract]:
    session = db.get_session()
    try:
        return (
            session.query(Contract)
            .options(joinedload(Contract.contagent))  # важно: без detached
            .filter(Contract.is_deleted == False)
            .order_by(Contract.date.desc())
            .all()
        )
    finally:
        session.close()


def get_deleted_contracts() -> list[Contract]:
    session = db.get_session()
    try:
        return (
            session.query(Contract)
            .options(joinedload(Contract.contagent))  # важно: без detached
            .filter(Contract.is_deleted == True)
            .order_by(Contract.date.desc())
            .all()
        )
    finally:
        session.close()


def get_contract_by_id(contract_id: int) -> Contract | None:
    session = db.get_session()
    try:
        return (
            session.query(Contract)
            .options(joinedload(Contract.contagent))
            .filter(Contract.id == contract_id)
            .first()
        )
    finally:
        session.close()


def get_contracts_by_contagent(contagent_id: int) -> list[Contract]:
    """Нужно для ui/contracts_window.py (и вообще полезно)."""
    session = db.get_session()
    try:
        return (
            session.query(Contract)
            .options(joinedload(Contract.contagent))
            .filter(
                Contract.is_deleted == False,
                Contract.contagent_id == contagent_id,
            )
            .order_by(Contract.date.desc())
            .all()
        )
    finally:
        session.close()


# =========================
# CRUD
# =========================

def create_contract(data: dict[str, Any]) -> int:
    session = db.get_session()
    try:
        obj = Contract(**data)
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return int(obj.id)
    finally:
        session.close()


def update_contract(contract_id: int, data: dict[str, Any]) -> None:
    session = db.get_session()
    try:
        obj = session.query(Contract).filter(Contract.id == contract_id).first()
        if not obj:
            raise ValueError("Договор не найден")

        for k, v in data.items():
            setattr(obj, k, v)

        session.commit()
    finally:
        session.close()


# =========================
# ARCHIVE
# =========================

def soft_delete_contract(contract_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Contract).filter(Contract.id == contract_id).first()
        if not obj:
            raise ValueError("Договор не найден")
        obj.is_deleted = True
        session.commit()
    finally:
        session.close()


def restore_contract(contract_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(Contract).filter(Contract.id == contract_id).first()
        if not obj:
            raise ValueError("Договор не найден")
        obj.is_deleted = False
        session.commit()
    finally:
        session.close()


def delete_contracts_forever(contract_ids: list[int]) -> None:
    if not contract_ids:
        return
    session = db.get_session()
    try:
        rows = session.query(Contract).filter(Contract.id.in_(contract_ids)).all()
        for r in rows:
            session.delete(r)
        session.commit()
    finally:
        session.close()


# =========================
# SEARCH (гибкий по токенам)
# =========================

def search_contracts(query: str) -> list[Contract]:
    session = db.get_session()
    try:
        q = (
            session.query(Contract)
            .options(joinedload(Contract.contagent))  # важно: без detached
            .join(Contagent, Contagent.id == Contract.contagent_id)
            .filter(Contract.is_deleted == False)
        )

        tokens = _tokens(query)
        for t in tokens:
            low = t.lower()
            q = q.filter(
                or_(
                    func.lower(Contract.number).like(f"%{low}%"),
                    func.lower(Contagent.name).like(f"%{low}%"),
                )
            )

        return q.order_by(Contract.date.desc()).all()
    finally:
        session.close()
