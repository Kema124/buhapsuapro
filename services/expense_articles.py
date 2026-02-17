from __future__ import annotations

import re
from typing import Any

from sqlalchemy import or_, func

import database.db as db
from database.models import ExpenseArticle

_TOKEN_RE = re.compile(r"\s+", re.UNICODE)


def _tokens(query: str) -> list[str]:
    q = (query or "").strip()
    if not q:
        return []
    return [t for t in _TOKEN_RE.split(q) if t][:20]


def get_all_expense_articles() -> list[ExpenseArticle]:
    session = db.get_session()
    try:
        return (
            session.query(ExpenseArticle)
            .filter(ExpenseArticle.is_deleted == False)
            .order_by(ExpenseArticle.name)
            .all()
        )
    finally:
        session.close()


def get_expense_article_by_id(article_id: int) -> ExpenseArticle | None:
    session = db.get_session()
    try:
        return session.query(ExpenseArticle).filter(ExpenseArticle.id == article_id).first()
    finally:
        session.close()


def get_deleted_expense_articles() -> list[ExpenseArticle]:
    session = db.get_session()
    try:
        return (
            session.query(ExpenseArticle)
            .filter(ExpenseArticle.is_deleted == True)
            .order_by(ExpenseArticle.name)
            .all()
        )
    finally:
        session.close()


def create_expense_article(data: dict[str, Any]) -> int:
    session = db.get_session()
    try:
        obj = ExpenseArticle(**data)
        obj.is_deleted = False
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return int(obj.id)
    finally:
        session.close()


def update_expense_article(article_id: int, data: dict[str, Any]) -> None:
    session = db.get_session()
    try:
        obj = session.query(ExpenseArticle).filter(
            ExpenseArticle.id == article_id,
            ExpenseArticle.is_deleted == False
        ).first()
        if not obj:
            raise ValueError("Статья расходов не найдена")
        for k, v in data.items():
            setattr(obj, k, v)
        session.commit()
    finally:
        session.close()


def soft_delete_expense_article(article_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(ExpenseArticle).filter(ExpenseArticle.id == article_id).first()
        if not obj:
            raise ValueError("Статья расходов не найдена")
        obj.is_deleted = True
        session.commit()
    finally:
        session.close()


def restore_expense_article(article_id: int) -> None:
    session = db.get_session()
    try:
        obj = session.query(ExpenseArticle).filter(ExpenseArticle.id == article_id).first()
        if not obj:
            raise ValueError("Статья расходов не найдена")
        obj.is_deleted = False
        session.commit()
    finally:
        session.close()


def delete_expense_articles_forever(article_ids: list[int]) -> None:
    if not article_ids:
        return
    session = db.get_session()
    try:
        session.query(ExpenseArticle).filter(ExpenseArticle.id.in_(article_ids)).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def search_expense_articles(query: str) -> list[ExpenseArticle]:
    session = db.get_session()
    try:
        q = session.query(ExpenseArticle).filter(ExpenseArticle.is_deleted == False)
        for token in _tokens(query):
            low = token.lower()
            q = q.filter(or_(
                func.lower(ExpenseArticle.name).like(f"%{low}%"),
                func.lower(func.coalesce(ExpenseArticle.group, "")).like(f"%{low}%"),
                func.lower(func.coalesce(ExpenseArticle.note, "")).like(f"%{low}%"),
            ))
        return q.order_by(ExpenseArticle.name).all()
    finally:
        session.close()


def filter_expense_articles(filters: dict[str, Any]) -> list[ExpenseArticle]:
    """Фильтр (как в 1С). Поддерживает: name, group_name."""
    session = db.get_session()
    try:
        q = session.query(ExpenseArticle).filter(ExpenseArticle.is_deleted == False)
        if filters.get("name"):
            low = str(filters["name"]).lower()
            q = q.filter(func.lower(ExpenseArticle.name).like(f"%{low}%"))
        if filters.get("group_name"):
            low = str(filters["group_name"]).lower()
            q = q.filter(func.lower(func.coalesce(ExpenseArticle.group_name, "")).like(f"%{low}%"))
        return q.order_by(ExpenseArticle.name).all()
    finally:
        session.close()
