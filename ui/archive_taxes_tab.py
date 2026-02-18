from __future__ import annotations

from typing import Any
from time import monotonic

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, QPoint

from services.taxes import (
    get_deleted_taxes, restore_tax, delete_taxes_forever
)


class ArchiveTaxesTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._confirm_deadline = 0.0

        self.main_layout = QVBoxLayout(self)

        btns = QHBoxLayout()
        self.restore_btn = QPushButton("Восстановить")
        self.delete_forever_btn = QPushButton("Удалить навсегда")
        btns.addWidget(self.restore_btn)
        btns.addWidget(self.delete_forever_btn)
        btns.addStretch()
        self.main_layout.addLayout(btns)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Наименование", "Ставка", "КБК", "Комментарий"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._menu)

        self.main_layout.addWidget(self.table)

        self.restore_btn.clicked.connect(self.restore_selected)
        self.delete_forever_btn.clicked.connect(self.delete_forever_selected)

        self.load_data()

    def _msg(self, text: str, kind: str = "info", timeout: int = 3500) -> None:
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def load_data(self) -> None:
        data = get_deleted_taxes()
        self.table.setRowCount(0)
        for r, t in enumerate(data):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(t.id))
            it_id.setData(Qt.ItemDataRole.UserRole, int(t.id))
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, QTableWidgetItem(str(getattr(t, "name", "") or "")))
            self.table.setItem(r, 2, QTableWidgetItem("" if t.rate is None else str(t.rate)))
            self.table.setItem(r, 3, QTableWidgetItem(t.kbk or ""))
            self.table.setItem(r, 4, QTableWidgetItem(t.note or ""))

    def selected_ids(self) -> list[int]:
        rows = {it.row() for it in self.table.selectedItems()}
        ids: list[int] = []
        for r in rows:
            item = self.table.item(r, 0)
            if not item:
                continue
            v: Any = item.data(Qt.ItemDataRole.UserRole)
            try:
                ids.append(int(v))
            except Exception:
                pass
        return ids

    def restore_selected(self) -> None:
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите налоги", "warning", 2500)
            return
        ok = 0
        for tid in ids:
            try:
                restore_tax(tid)
                ok += 1
            except Exception as e:
                self._msg(f"Не удалось восстановить {tid}: {e}", "error", 6000)
        self.load_data()
        self._msg(f"Восстановлено: {ok}", "success", 3000)

    def delete_forever_selected(self) -> None:
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите налоги", "warning", 2500)
            return

        now = monotonic()
        if now > self._confirm_deadline:
            self._confirm_deadline = now + 5.0
            self._msg(f"Повторите “Удалить навсегда” в течение 5 секунд (выбрано: {len(ids)})", "warning", 5000)
            return

        try:
            delete_taxes_forever(ids)
            self.load_data()
            self._msg(f"Удалено навсегда: {len(ids)}", "success", 3500)
        except Exception as e:
            self._msg(str(e), "error", 7000)

    def _menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        a_restore = menu.addAction("Восстановить")
        a_delete = menu.addAction("Удалить навсегда")
        menu.addSeparator()
        a_refresh = menu.addAction("Обновить")
        act = menu.exec(self.table.viewport().mapToGlobal(pos))
        if act == a_restore:
            self.restore_selected()
        elif act == a_delete:
            self.delete_forever_selected()
        elif act == a_refresh:
            self.load_data()
            self._msg("Обновлено", "success", 1500)
