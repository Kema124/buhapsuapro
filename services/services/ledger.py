from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from database.db import get_session
from database.models import LedgerEntry


def get_entries_for_recorder(recorder_type: str, recorder_id: int) -> list[LedgerEntry]:
    session = get_session()
    try:
        return (
            session.query(LedgerEntry)
            .filter(LedgerEntry.recorder_type == str(recorder_type))
            .filter(LedgerEntry.recorder_id == int(recorder_id))
            .order_by(LedgerEntry.period, LedgerEntry.id)
            .all()
        )
    finally:
        session.close()


def delete_entries_for_recorder(recorder_type: str, recorder_id: int, *, session: Session | None = None) -> int:
    own = session is None
    s = session or get_session()
    try:
        q = (
            s.query(LedgerEntry)
            .filter(LedgerEntry.recorder_type == str(recorder_type))
            .filter(LedgerEntry.recorder_id == int(recorder_id))
        )
        n = q.count()
        q.delete(synchronize_session=False)
        if own:
            s.commit()
        return int(n)
    except Exception:
        if own:
            s.rollback()
        raise
    finally:
        if own:
            s.close()


def create_entry(
    *,
    period: datetime,
    recorder_type: str,
    recorder_id: int,
    account_dr_id: int,
    account_cr_id: int,
    amount: Decimal,
    description: str | None = None,
    subconto_dr_1: int | None = None,
    subconto_dr_2: int | None = None,
    subconto_dr_3: int | None = None,
    subconto_cr_1: int | None = None,
    subconto_cr_2: int | None = None,
    subconto_cr_3: int | None = None,
    session: Session | None = None,
) -> int:
    own = session is None
    s = session or get_session()
    try:
        e = LedgerEntry(
            period=period,
            recorder_type=str(recorder_type),
            recorder_id=int(recorder_id),
            account_dr_id=int(account_dr_id),
            account_cr_id=int(account_cr_id),
            amount=amount,
            description=description,
            subconto_dr_1=subconto_dr_1,
            subconto_dr_2=subconto_dr_2,
            subconto_dr_3=subconto_dr_3,
            subconto_cr_1=subconto_cr_1,
            subconto_cr_2=subconto_cr_2,
            subconto_cr_3=subconto_cr_3,
        )
        s.add(e)
        if own:
            s.commit()
            s.refresh(e)
        return int(e.id)
    except Exception:
        if own:
            s.rollback()
        raise
    finally:
        if own:
            s.close()
