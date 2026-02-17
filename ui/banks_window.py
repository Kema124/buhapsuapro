from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, QPoint

from services.banks import (
    get_all_banks, search_banks, filter_banks, soft_delete_bank
)


class BanksWindow(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Банки")
        self.resize(1000, 550)

        self._init_ui()
        self.load_data()

    def _msg(self, text: str, kind: str = "info", timeout: int = 3500) -> None:
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def _init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск: банк / БИК / SWIFT")
        self.search_input.textChanged.connect(self.on_search)
        top.addWidget(self.search_input, 1)

        self.filter_btn = QPushButton("Фильтр")
        self.filter_btn.clicked.connect(self.toggle_filter)
        top.addWidget(self.filter_btn)

        self.btn_add = QPushButton("Создать")
        self.btn_edit = QPushButton("Открыть")
        self.btn_copy = QPushButton("Копировать")
        self.btn_archive = QPushButton("В архив")
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_copy)
        top.addWidget(self.btn_archive)

        self.main_layout.addLayout(top)

        from ui.one_c_filter import OneCFilterPanel, FilterField

        self.filter_panel = OneCFilterPanel([
            FilterField("name", "Наименование"),
            FilterField("country", "Страна", kind="combo", items=[
                ("Все", None),
                ("Россия", "RU"),
                ("Абхазия", "AB"),
            ]),
            FilterField("bik", "БИК"),
            FilterField("swift", "SWIFT"),
        ])
        self.filter_panel.setObjectName("FilterPanel")
        self.filter_panel.applied.connect(self._on_filter_applied)
        self.filter_panel.reset.connect(self._on_filter_reset)
        self.filter_panel.setVisible(False)
        self.main_layout.addWidget(self.filter_panel)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Страна", "Наименование", "БИК", "SWIFT"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._menu)
        self.table.doubleClicked.connect(self.edit_selected)

        self.main_layout.addWidget(self.table)

        # TODO: формы банков (следующим этапом). Сейчас только архивирование.
        self.btn_archive.clicked.connect(self.archive_selected)
        self.btn_edit.clicked.connect(self.edit_selected)
        self.btn_copy.clicked.connect(lambda: self._msg("Копирование банков — позже", "info", 3500))
        self.btn_add.clicked.connect(lambda: self._msg("Создание банков — позже", "info", 3500))

    def toggle_filter(self) -> None:
        self.filter_panel.setVisible(not self.filter_panel.isVisible())

    def load_data(self) -> None:
        self._fill(get_all_banks())

    def _fill(self, items) -> None:
        self.table.setRowCount(0)
        for r, b in enumerate(items):
            self.table.insertRow(r)
            it_id = QTableWidgetItem(str(b.id))
            it_id.setData(Qt.ItemDataRole.UserRole, int(b.id))
            self.table.setItem(r, 0, it_id)
            self.table.setItem(r, 1, QTableWidgetItem("Россия" if b.country == "RU" else "Абхазия"))
            self.table.setItem(r, 2, QTableWidgetItem(b.name))
            self.table.setItem(r, 3, QTableWidgetItem(b.bik or ""))
            self.table.setItem(r, 4, QTableWidgetItem(b.swift or ""))

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

    def on_search(self, text: str) -> None:
        q = (text or "").strip()
        self._fill(search_banks(q) if q else get_all_banks())

    def _on_filter_applied(self, filters: dict) -> None:
        self._fill(filter_banks(filters))

    def _on_filter_reset(self) -> None:
        self.load_data()

    def archive_selected(self) -> None:
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите банки", "warning", 2500)
            return
        ok = 0
        for bid in ids:
            try:
                soft_delete_bank(bid)
                ok += 1
            except Exception as e:
                self._msg(f"Не удалось архивировать {bid}: {e}", "error", 6000)
        self.load_data()
        self._msg(f"Перемещено в архив: {ok}", "success", 3000)

    def edit_selected(self) -> None:
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите банк", "warning", 2500)
            return
        self._msg("Форма банка — на следующем этапе", "info", 3500)

    def _menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        a_add = menu.addAction("Создать")
        a_open = menu.addAction("Открыть")
        a_copy = menu.addAction("Копировать")
        menu.addSeparator()
        a_arch = menu.addAction("В архив")
        menu.addSeparator()
        a_refresh = menu.addAction("Обновить")

        act = menu.exec(self.table.viewport().mapToGlobal(pos))
        if act == a_add:
            self._msg("Создание банков — позже", "info", 3500)
        elif act == a_open:
            self.edit_selected()
        elif act == a_copy:
            self._msg("Копирование банков — позже", "info", 3500)
        elif act == a_arch:
            self.archive_selected()
        elif act == a_refresh:
            self.load_data()
            self._msg("Обновлено", "success", 1500)
