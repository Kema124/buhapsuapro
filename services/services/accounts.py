from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import or_

from database.db import get_session
from database.models import Account


def seed_default_accounts_if_empty() -> None:
    """Создаёт минимальный план счетов.

    Мы не навязываем конкретный «официальный» план (в Абхазии могут быть
    нюансы), но даём стартовый набор, чтобы можно было проводить документы.
    """
    session = get_session()
    try:
        exists = session.query(Account).first()
        if exists is not None:
            return

        defaults = [
            ("50", "Касса", "active"),
            ("51", "Расчетные счета", "active"),
            ("60", "Расчеты с поставщиками", "passive"),
            ("62", "Расчеты с покупателями", "active"),
            ("68", "Расчеты по налогам и сборам", "passive"),
            ("70", "Расчеты с персоналом по оплате труда", "passive"),
            ("90.01", "Выручка", "passive"),
            ("90.02", "Себестоимость продаж", "active"),
            ("91.01", "Прочие доходы", "passive"),
            ("91.02", "Прочие расходы", "active"),
        ]

        for code, name, acc_type in defaults:
            session.add(Account(code=code, name=name, account_type=acc_type))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_all_accounts(include_deleted: bool = False) -> list[Account]:
    session = get_session()
    try:
        q = session.query(Account)
        if not include_deleted:
            q = q.filter(Account.is_deleted.is_(False))
        return q.order_by(Account.code).all()
    finally:
        session.close()


def search_accounts(text: str) -> list[Account]:
    s = (text or "").strip()
    session = get_session()
    try:
        if not s:
            return get_all_accounts()
        like = f"%{s}%"
        return (
            session.query(Account)
            .filter(Account.is_deleted.is_(False))
            .filter(or_(Account.code.ilike(like), Account.name.ilike(like)))
            .order_by(Account.code)
            .all()
        )
    finally:
        session.close()


def create_account(data: Mapping[str, Any]) -> int:
    session = get_session()
    try:
        acc = Account(**dict(data))
        session.add(acc)
        session.commit()
        session.refresh(acc)
        return int(acc.id)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
