"""Миграция: добавить is_deleted в contracts.

Запуск:
  python migrations/002_add_is_deleted_contracts.py /path/to/accounting.db

Если путь не указан, используйте переменную окружения BUH_DB_PATH.
"""

from __future__ import annotations

import os
import sqlite3
import sys


def main() -> int:
    db_path = None
    if len(sys.argv) >= 2:
        db_path = sys.argv[1]
    if not db_path:
        db_path = os.environ.get("BUH_DB_PATH")

    if not db_path:
        print("Укажите путь к базе: python migrations/002_add_is_deleted_contracts.py /path/to/accounting.db")
        return 2

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE contracts ADD COLUMN is_deleted INTEGER DEFAULT 0")
        print("OK: добавлено поле is_deleted в contracts")
    except Exception as e:
        print("Поле уже добавлено или ошибка:", e)
    finally:
        conn.commit()
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

