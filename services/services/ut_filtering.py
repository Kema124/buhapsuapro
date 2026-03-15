from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.sql.sqltypes import Boolean as SAT_Boolean, Date as SAT_Date, Integer as SAT_Integer, Numeric as SAT_Numeric
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import ColumnElement


def _to_bool(v: Any) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "да", "истина"):
        return True
    if s in ("0", "false", "no", "нет", "ложь"):
        return False
    return None


def _parse_date(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    s = str(v).strip()
    if not s:
        return None
    # поддержим "YYYY-MM-DD" (основной кейс)
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _coerce_value(col, value: Any) -> Any:
    """Привести значение к типу колонки (best-effort).

    Это важно, потому что виджет отборов отдаёт строки.
    """
    if value is None:
        return None

    t = getattr(col, "type", None)
    try:
        if isinstance(t, SAT_Boolean):
            b = _to_bool(value)
            return b if b is not None else value
        if isinstance(t, SAT_Date):
            d = _parse_date(value)
            return d if d is not None else value
        if isinstance(t, (SAT_Integer,)):
            return int(value)
        if isinstance(t, (SAT_Numeric,)):
            return float(value)
    except Exception:
        return value

    return value


def build_expression(model, cond: dict[str, Any]) -> ColumnElement[bool] | None:
    """
    cond = {"type":"cond","field":"name","cmp":"contains","value":"abc"}
    """
    field = cond.get("field")
    cmp_ = cond.get("cmp")
    value = cond.get("value")

    if not field or not cmp_:
        return None

    col = getattr(model, field, None)
    if col is None:
        return None

    if cmp_ == "is_null":
        return col.is_(None)
    if cmp_ == "not_null":
        return col.is_not(None)

    value = _coerce_value(col, value)

    if cmp_ == "eq":
        # для bool лучше is_ / is_not
        if isinstance(getattr(col, "type", None), SAT_Boolean):
            b = _to_bool(value)
            if b is not None:
                return col.is_(b)
        return col == value
    if cmp_ == "neq":
        if isinstance(getattr(col, "type", None), SAT_Boolean):
            b = _to_bool(value)
            if b is not None:
                return col.is_not(b)
        return col != value

    if value is None:
        return None

    # strings
    if cmp_ == "contains":
        return col.ilike(f"%{value}%")
    if cmp_ == "not_contains":
        return ~col.ilike(f"%{value}%")
    if cmp_ == "starts":
        return col.ilike(f"{value}%")
    if cmp_ == "ends":
        return col.ilike(f"%{value}")

    # numeric/date comparisons (value might be string)
    if cmp_ in ("gt", "gte", "lt", "lte"):
        v_any = _coerce_value(col, value)

        if cmp_ == "gt":
            return col > v_any
        if cmp_ == "gte":
            return col >= v_any
        if cmp_ == "lt":
            return col < v_any
        if cmp_ == "lte":
            return col <= v_any

    return None


def build_group_expression(model, spec: dict[str, Any]) -> ColumnElement[bool] | None:
    """
    spec root/group:
      {"type":"group","op":"AND|OR","items":[cond/group,...]}
    """
    if not spec:
        return None
    op = (spec.get("op") or "AND").upper()
    items = spec.get("items") or []

    parts: list[ColumnElement[bool]] = []
    for it in items:
        t = it.get("type")
        if t == "group":
            ex = build_group_expression(model, it)
        else:
            ex = build_expression(model, it)
        if ex is not None:
            parts.append(ex)

    if not parts:
        return None

    if op == "OR":
        return or_(*parts)
    return and_(*parts)


def apply_ut_filter(query: Query, model, spec: dict[str, Any]) -> Query:
    expr = build_group_expression(model, spec)
    if expr is None:
        return query
    return query.filter(expr)
