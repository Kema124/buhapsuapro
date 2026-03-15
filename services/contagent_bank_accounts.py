from __future__ import annotations

from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

import database.db as db
from database.models import ContagentBankAccount


def get_accounts_by_contagent(contagent_id: int) -> list[ContagentBankAccount]:
    session = db.get_session()
    try:
        return (
            session.query(ContagentBankAccount).options(joinedload(ContagentBankAccount.bank))
            .filter(
                and_(
                    ContagentBankAccount.contagent_id == contagent_id,
                    ContagentBankAccount.is_deleted.is_(False),
                )
            )
            .order_by(ContagentBankAccount.id.asc())
            .all()
        )
    finally:
        session.close()


def create_bank_account(data: dict[str, Any]) -> int:
    session = db.get_session()
    try:
        obj = ContagentBankAccount(**data)
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return int(obj.id)
    finally:
        session.close()


def update_bank_account(account_id: int, data: dict[str, Any]) -> None:
    session = db.get_session()
    try:
        obj = (
            session.query(ContagentBankAccount).options(joinedload(ContagentBankAccount.bank))
            .filter(ContagentBankAccount.id == account_id)
            .first()
        )
        if not obj:
            raise ValueError("Банковский счёт не найден")

        for k, v in data.items():
            setattr(obj, k, v)

        session.commit()
    finally:
        session.close()


def delete_bank_account(account_id: int) -> None:
    session = db.get_session()
    try:
        obj = (
            session.query(ContagentBankAccount).options(joinedload(ContagentBankAccount.bank))
            .filter(ContagentBankAccount.id == account_id)
            .first()
        )
        if not obj:
            return
        obj.is_deleted = True
        session.commit()
    finally:
        session.close()
