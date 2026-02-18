from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QPoint, Signal

from ui.assets import load_icon
from ui.theme_manager import ThemeManager
from ui.ut_filter_panel import UTFilterPanel, FilterField

from services.banks import get_all_banks, search_banks, soft_delete_bank, filter_banks_ut


class BanksWindow(QWidget):
    data_changed = Signal()

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._theme = ThemeManager.current()

        self.setWindowTitle("Банки")
        self.resize(1000, 550)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)

        self._init_ui()

        ThemeManager.subscribe(self._on_theme_changed)
        self.apply_icons()

        self.load_data()

    def closeEvent(self, event):
        ThemeManager.unsubscribe(self._on_theme_changed)
        super().closeEvent(event)

    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------

    def _safe_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    def _msg(self, text: str, kind: str = "info", timeout: int = 3000) -> None:
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _init_ui(self):
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск: название / БИК / SWIFT / адрес")
        self.search.textChanged.connect(lambda _t: self._search_timer.start(250))
        top.addWidget(self.search)
        lay.addLayout(top)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Создать")
        self.btn_edit = QPushButton("Изменить")
        self.btn_copy = QPushButton("Копировать")
        self.btn_del = QPushButton("В архив")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_edit)
        btns.addWidget(self.btn_copy)
        btns.addWidget(self.btn_del)
        btns.addStretch(1)
        lay.addLayout(btns)

        self.btn_add.clicked.connect(self.add_item)
        self.btn_edit.clicked.connect(self.edit_item)
        self.btn_copy.clicked.connect(self.copy_item)
        self.btn_del.clicked.connect(self.archive_selected)

        # УТ-фильтр (Отбор)
        self.filter_panel = UTFilterPanel(fields=[
            FilterField("name", "Название", "str"),
            FilterField("country", "Страна", "enum", choices=[
                ("Россия", "RU"),
                ("Абхазия", "ABH"),
            ]),
            FilterField("bik", "БИК", "str"),
            FilterField("swift", "SWIFT", "str"),
            FilterField("is_active", "Активен", "bool", choices=[
                ("Да", True),
                ("Нет", False),
            ]),
        ])
        self.filter_panel.applied.connect(self._apply_ut_filter)
        self.filter_panel.reset.connect(self._reset_ut_filter)
        lay.addWidget(self.filter_panel)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Страна", "Наименование", "БИК", "SWIFT"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._menu)
        self.table.doubleClicked.connect(self.edit_item)

        lay.addWidget(self.table)

    # ---------------------------------------------------------
    # theme / icons
    # ---------------------------------------------------------

    def apply_icons(self):
        c = "#ffffff" if self._theme == "dark" else "#22324a"
        self.btn_add.setIcon(load_icon("add.svg", color=c))
        self.btn_edit.setIcon(load_icon("edit.svg", color=c))
        self.btn_copy.setIcon(load_icon("copy.svg", color=c))
        self.btn_del.setIcon(load_icon("archive.svg", color=c))

    def _on_theme_changed(self, theme: str):
        self._theme = theme
        self.apply_icons()

    # ---------------------------------------------------------
    # filter
    # ---------------------------------------------------------

    def toggle_filter(self) -> None:
        self.filter_panel.toggle()

    def _apply_ut_filter(self, spec: dict) -> None:
        self._fill(filter_banks_ut(spec))

    def _reset_ut_filter(self) -> None:
        self.load_data()

    # ---------------------------------------------------------
    # data
    # ---------------------------------------------------------

    def load_data(self):
        self._fill(get_all_banks())

    def _fill(self, items):
        self.table.setRowCount(0)
        for r, b in enumerate(items):
            self.table.insertRow(r)

            it_id = QTableWidgetItem(str(getattr(b, "id", "")))
            bid = self._safe_int(getattr(b, "id", None))
            it_id.setData(Qt.ItemDataRole.UserRole, bid if bid is not None else 0)
            self.table.setItem(r, 0, it_id)

            country = getattr(b, "country", None)
            self.table.setItem(r, 1, QTableWidgetItem("Россия" if country == "RU" else "Абхазия"))
            self.table.setItem(r, 2, QTableWidgetItem(getattr(b, "name", "") or ""))
            self.table.setItem(r, 3, QTableWidgetItem(getattr(b, "bik", "") or ""))
            self.table.setItem(r, 4, QTableWidgetItem(getattr(b, "swift", "") or ""))

    # ---------------------------------------------------------
    # selection
    # ---------------------------------------------------------

    def _selected_ids(self) -> list[int]:
        rows = {it.row() for it in self.table.selectedItems()}
        ids: list[int] = []
        for row in rows:
            item = self.table.item(row, 0)
            if item is None:
                continue
            val: Any = item.data(Qt.ItemDataRole.UserRole)
            cid = self._safe_int(val)
            if cid is not None:
                ids.append(cid)
        return ids

    def _selected_id(self) -> int | None:
        ids = self._selected_ids()
        return ids[0] if ids else None

    # ---------------------------------------------------------
    # search
    # ---------------------------------------------------------

    def _do_search(self):
        q = self.search.text().strip()
        self._fill(search_banks(q) if q else get_all_banks())

    # ---------------------------------------------------------
    # context menu
    # ---------------------------------------------------------

    def _menu(self, pos: QPoint):
        menu = QMenu(self)
        a_add = menu.addAction("Создать")
        a_edit = menu.addAction("Изменить")
        a_copy = menu.addAction("Копировать")
        menu.addSeparator()
        a_arch = menu.addAction("В архив")

        act = menu.exec(self.table.viewport().mapToGlobal(pos))
        if act == a_add:
            self.add_item()
        elif act == a_edit:
            self.edit_item()
        elif act == a_copy:
            self.copy_item()
        elif act == a_arch:
            self.archive_selected()

    # ---------------------------------------------------------
    # actions
    # ---------------------------------------------------------

    def add_item(self):
        from ui.bank_form import BankForm
        dlg = BankForm(main_window=self.main_window, mode="create", on_saved=self.load_data)
        dlg.exec()

    def edit_item(self):
        bank_id = self._selected_id()
        if bank_id is None:
            self._msg("Выберите банк", "warning", 3000)
            return
        from ui.bank_form import BankForm
        dlg = BankForm(main_window=self.main_window, bank_id=bank_id, mode="edit", on_saved=self.load_data)
        dlg.exec()

    def copy_item(self):
        bank_id = self._selected_id()
        if bank_id is None:
            self._msg("Выберите банк", "warning", 3000)
            return
        from ui.bank_form import BankForm
        dlg = BankForm(main_window=self.main_window, bank_id=bank_id, mode="copy", on_saved=self.load_data)
        dlg.exec()

    def archive_selected(self):
        ids = self._selected_ids()
        if not ids:
            self._msg("Выберите банки", "warning", 3000)
            return

        for i in ids:
            try:
                soft_delete_bank(i)
            except Exception as e:
                self._msg(str(e), "error", 6000)

        self.load_data()
        self._msg(f"Перемещено в архив: {len(ids)}", "success", 3000)
