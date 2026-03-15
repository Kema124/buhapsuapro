from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database.uow import UnitOfWork
from database.db import get_session
from database.models import Account, BankReceipt
from services.ledger import create_entry, delete_entries_for_recorder


RECORDER_TYPE_BANK_RECEIPT = "doc_bank_receipt"


def _get_account_id_by_code(session, code: str) -> int:
    acc = session.query(Account).filter(Account.code == code).first()
    if not acc:
        raise ValueError(f"Не найден счет {code} в плане счетов")
    return int(acc.id)


def get_bank_receipts() -> list[BankReceipt]:
    session = get_session()
    try:
        return (
            session.query(BankReceipt)
            .options(joinedload(BankReceipt.contagent), joinedload(BankReceipt.contract))
            .filter(BankReceipt.is_deleted.is_(False))
            .order_by(BankReceipt.date.desc(), BankReceipt.id.desc())
            .all()
        )
    finally:
        session.close()


def search_bank_receipts(text: str) -> list[BankReceipt]:
    s = (text or "").strip()
    session = get_session()
    try:
        q = (
            session.query(BankReceipt)
            .options(joinedload(BankReceipt.contagent), joinedload(BankReceipt.contract))
            .filter(BankReceipt.is_deleted.is_(False))
        )
        if s:
            like = f"%{s}%"
            q = q.filter(or_(BankReceipt.number.ilike(like), BankReceipt.purpose.ilike(like)))
        return q.order_by(BankReceipt.date.desc(), BankReceipt.id.desc()).all()
    finally:
        session.close()


def get_bank_receipt_by_id(rid: int) -> BankReceipt | None:
    session = get_session()
    try:
        return (
            session.query(BankReceipt)
            .options(joinedload(BankReceipt.contagent), joinedload(BankReceipt.contract))
            .filter(BankReceipt.id == int(rid))
            .first()
        )
    finally:
        session.close()


def create_bank_receipt(data: Mapping[str, Any]) -> int:
    session = get_session()
    try:
        r = BankReceipt(**dict(data))
        session.add(r)
        session.commit()
        session.refresh(r)
        return int(r.id)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_bank_receipt(rid: int, data: Mapping[str, Any]) -> None:
    session = get_session()
    try:
        r = session.query(BankReceipt).filter(BankReceipt.id == int(rid)).first()
        if not r:
            raise ValueError("Документ не найден")
        for k, v in dict(data).items():
            setattr(r, k, v)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def archive_bank_receipts(ids: list[int]) -> int:
    if not ids:
        return 0
    session = get_session()
    try:
        q = session.query(BankReceipt).filter(BankReceipt.id.in_([int(x) for x in ids]))
        n = 0
        for r in q.all():
            r.is_deleted = True
            n += 1
        session.commit()
        return int(n)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def post_bank_receipt(rid: int) -> None:
    """Проведение: Дт 51 Кт 62 (поступление от покупателя).

    Специфика: на этом этапе проводка шаблонная. Дальше будет выбор операции/счетов.
    Аналитика: на стороне кредита (62) ставим subconto_cr_1=contagent_id, subconto_cr_2=contract_id.
    """

    with UnitOfWork() as uow:
        s = uow.session
        r = s.query(BankReceipt).filter(BankReceipt.id == int(rid)).with_for_update().first()
        if not r:
            raise ValueError("Документ не найден")
        if r.status == "posted":
            return

        # перепроведение: очистить старые записи
        delete_entries_for_recorder(RECORDER_TYPE_BANK_RECEIPT, int(r.id), session=s)

        acc_51 = _get_account_id_by_code(s, "51")
        acc_62 = _get_account_id_by_code(s, "62")

        create_entry(
            period=datetime.combine(r.date, datetime.now().time()),
            recorder_type=RECORDER_TYPE_BANK_RECEIPT,
            recorder_id=int(r.id),
            account_dr_id=acc_51,
            account_cr_id=acc_62,
            amount=Decimal(r.amount),
            description=r.purpose,
            subconto_cr_1=int(r.contagent_id) if r.contagent_id else None,
            subconto_cr_2=int(r.contract_id) if r.contract_id else None,
            session=s,
        )

        r.status = "posted"
        r.posted_at = datetime.now()
        uow.commit()


def unpost_bank_receipt(rid: int) -> None:
    with UnitOfWork() as uow:
        s = uow.session
        r = s.query(BankReceipt).filter(BankReceipt.id == int(rid)).with_for_update().first()
        if not r:
            raise ValueError("Документ не найден")

        delete_entries_for_recorder(RECORDER_TYPE_BANK_RECEIPT, int(r.id), session=s)
        r.status = "draft"
        r.posted_at = None
        uow.commit()
