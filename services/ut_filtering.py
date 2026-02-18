from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from sqlalchemy import and_, or_
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

    # normalize bool
    if isinstance(getattr(col, "type", None), object):
        # best-effort: leave as is
        pass

    if cmp_ == "eq":
        return col == value
    if cmp_ == "neq":
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
        try:
            v_num = int(value)
            v_any = v_num
        except Exception:
            v_any = value

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
