from __future__ import annotations

from sqlalchemy import Engine, text

from database.db import Base
from services.accounts import seed_default_accounts_if_empty


def _has_column(engine: Engine, table: str, column: str) -> bool:
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return any(r[1] == column for r in rows)  # (cid, name, type, notnull, dflt_value, pk)

    # generic (PostgreSQL etc.)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :t
                """
            ),
            {"t": table},
        ).fetchall()
    return any(r[0] == column for r in rows)


def _add_column(engine: Engine, table: str, ddl: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def ensure_schema(engine: Engine) -> None:
    """Ensure DB schema is compatible with current code.

    We do *not* use Alembic yet. For now we:
    1) create missing tables (safe)
    2) add missing columns that are required for new features
    """

    # 1) tables
    Base.metadata.create_all(bind=engine)

    # Минимальный план счетов, чтобы «проведение» работало из коробки
    try:
        seed_default_accounts_if_empty()
    except Exception:
        # не критично для старта приложения
        pass

    # 2) columns
    # invoices: direction (in/out). Older DBs may not have this field.
    # (Older DBs may have invoices without these fields.)
    try:
        if _has_column(engine, "invoices", "direction") is False:
            _add_column(engine, "invoices", "direction VARCHAR(10) DEFAULT 'out' NOT NULL")
    except Exception:
        # If invoices table doesn't exist yet, create_all above handles it.
        # Any other issue should be visible during DB access.
        pass

    # contagents: structured addresses / geo
    try:
        if _has_column(engine, "contagents", "legal_address") is False:
            _add_column(engine, "contagents", "legal_address VARCHAR")
        if _has_column(engine, "contagents", "legal_address_json") is False:
            _add_column(engine, "contagents", "legal_address_json VARCHAR")
        if _has_column(engine, "contagents", "factual_address") is False:
            _add_column(engine, "contagents", "factual_address VARCHAR")
        if _has_column(engine, "contagents", "factual_address_json") is False:
            _add_column(engine, "contagents", "factual_address_json VARCHAR")
        if _has_column(engine, "contagents", "geo_lat") is False:
            _add_column(engine, "contagents", "geo_lat VARCHAR(50)")
        if _has_column(engine, "contagents", "geo_lon") is False:
            _add_column(engine, "contagents", "geo_lon VARCHAR(50)")
    except Exception:
        pass

    # accounts: is_folder
    try:
        if _has_column(engine, "accounts", "is_folder") is False:
            _add_column(engine, "accounts", "is_folder BOOLEAN DEFAULT 0")
    except Exception:
        pass

    # ledger_entries: new reg format (period/recorder/analytics)
    # For old DBs, we add missing columns. (Type changes are left as-is on SQLite.)
    try:
        if _has_column(engine, "ledger_entries", "period") is False:
            _add_column(engine, "ledger_entries", "period DATETIME")
        if _has_column(engine, "ledger_entries", "recorder_type") is False:
            _add_column(engine, "ledger_entries", "recorder_type VARCHAR(50)")
        if _has_column(engine, "ledger_entries", "recorder_id") is False:
            _add_column(engine, "ledger_entries", "recorder_id INTEGER")
        if _has_column(engine, "ledger_entries", "account_dr_id") is False:
            _add_column(engine, "ledger_entries", "account_dr_id INTEGER")
        if _has_column(engine, "ledger_entries", "account_cr_id") is False:
            _add_column(engine, "ledger_entries", "account_cr_id INTEGER")
        for c in (
            "subconto_dr_1",
            "subconto_dr_2",
            "subconto_dr_3",
            "subconto_cr_1",
            "subconto_cr_2",
            "subconto_cr_3",
        ):
            if _has_column(engine, "ledger_entries", c) is False:
                _add_column(engine, "ledger_entries", f"{c} INTEGER")
    except Exception:
        pass
