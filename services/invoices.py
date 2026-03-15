from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from database.db import get_session
from database.models import PaymentInvoice


STATUS_DRAFT = "draft"
STATUS_POSTED = "posted"
STATUS_CANCELED = "canceled"


def get_invoice_by_id(invoice_id: int) -> PaymentInvoice | None:
    session = get_session()
    try:
        return session.query(PaymentInvoice).filter(PaymentInvoice.id == int(invoice_id)).first()
    finally:
        session.close()


def get_invoices(direction: str) -> list[PaymentInvoice]:
    session = get_session()
    try:
        return (
            session.query(PaymentInvoice)
            .filter(PaymentInvoice.direction == str(direction))
            .order_by(PaymentInvoice.date.desc(), PaymentInvoice.id.desc())
            .all()
        )
    finally:
        session.close()


def search_invoices(direction: str, text: str) -> list[PaymentInvoice]:
    s = (text or "").strip()
    if not s:
        return get_invoices(direction)

    like = f"%{s}%"
    session = get_session()
    try:
        return (
            session.query(PaymentInvoice)
            .filter(PaymentInvoice.direction == str(direction))
            .filter(PaymentInvoice.number.ilike(like))
            .order_by(PaymentInvoice.date.desc(), PaymentInvoice.id.desc())
            .all()
        )
    finally:
        session.close()


def create_invoice(data: Mapping[str, Any]) -> int:
    session = get_session()
    try:
        inv = PaymentInvoice(**dict(data))
        session.add(inv)
        session.commit()
        session.refresh(inv)
        return int(inv.id)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_invoice(invoice_id: int, data: Mapping[str, Any]) -> None:
    session = get_session()
    try:
        inv = session.query(PaymentInvoice).filter(PaymentInvoice.id == int(invoice_id)).first()
        if inv is None:
            raise ValueError("Счет не найден")
        for k, v in dict(data).items():
            setattr(inv, k, v)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _default_accounts_for_direction(direction: str) -> tuple[int | None, int | None]:
    """Подберём дефолтные счета по коду (если есть)."""
    accs = get_all_accounts()
    by_code = {a.code: a for a in accs}

    if direction == "out":
        # Дт 62 Кт 90.01
        d = by_code.get("62")
        c = by_code.get("90.01")
        return (d.id if d else None, c.id if c else None)
    # in: Дт 90.02 (или расходы) Кт 60
    d = by_code.get("90.02")
    c = by_code.get("60")
    return (d.id if d else None, c.id if c else None)

