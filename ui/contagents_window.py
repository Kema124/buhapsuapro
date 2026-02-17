from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QMenu,
    QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer

from ui.assets import load_icon
from ui.theme_manager import ThemeManager

from services.contagents import (
    get_all_contagents,
    search_contagents,
    soft_delete_contagent
)


class ContagentsWindow(QWidget):
    data_changed = Signal()

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._theme = ThemeManager.current()

        self.setWindowTitle("Контрагенты")
        self.resize(1000, 550)

        self._init_ui()

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)

        ThemeManager.subscribe(self._on_theme_changed)
        self.apply_icons()

        self.load_data()

    def closeEvent(self, event):
        ThemeManager.unsubscribe(self._on_theme_changed)
        super().closeEvent(event)

    def _msg(self, text: str, kind: str = "info", timeout: int = 3000):
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def _icon_color(self) -> str:
        return "#e8eef7" if self._theme == "dark" else "#22324a"

    def apply_icons(self) -> None:
        c = self._icon_color()
        self.filter_btn.setIcon(load_icon("filter.svg", color=c))
        self.add_btn.setIcon(load_icon("add.svg", color=c))
        self.edit_btn.setIcon(load_icon("edit.svg", color=c))
        self.copy_btn.setIcon(load_icon("copy.svg", color=c))
        self.delete_btn.setIcon(load_icon("archive.svg", color=c))

    def _on_theme_changed(self, theme: str) -> None:
        self._theme = theme
        self.apply_icons()

    def _init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)

        # search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск: имя, ИНН, КПП, адрес, телефон, email. Пример: inn:12345678")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        self.main_layout.addLayout(search_layout)

        # buttons
        btn_layout = QHBoxLayout()
        self.filter_btn = QPushButton("Фильтр")
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.copy_btn = QPushButton("Копировать")
        self.delete_btn = QPushButton("В архив")

        btn_layout.addWidget(self.filter_btn)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)

        self.filter_btn.clicked.connect(self.toggle_filter)
        self.add_btn.clicked.connect(self.add_contagent)
        self.edit_btn.clicked.connect(self.edit_contagent)
        self.copy_btn.clicked.connect(self.copy_contagent)
        self.delete_btn.clicked.connect(self.soft_delete_selected)

        # filter panel (1C)
        from ui.one_c_filter import OneCFilterPanel, FilterField

        self.filter_panel = OneCFilterPanel([
            FilterField("name", "Название", placeholder=""),
            FilterField("inn", "ИНН", placeholder=""),
            FilterField("role", "Роль", kind="combo", items=[
                ("Все", None),
                ("Покупатель", "buyer"),
                ("Поставщик", "supplier"),
                ("Оба", "both"),
            ]),
            FilterField("organization_type", "Тип", kind="combo", items=[
                ("Все", None),
                ("Юр. лицо", "company"),
                ("ИП", "ip"),
                ("Физ. лицо", "person"),
            ]),
            FilterField("is_active", "Активность", kind="combo", items=[
                ("Все", None),
                ("Активные", True),
                ("Неактивные", False),
            ]),
        ])
        self.filter_panel.setObjectName("FilterPanel")
        self.filter_panel.applied.connect(self._on_filter_applied)
        self.filter_panel.reset.connect(self._on_filter_reset)

        self.filter_panel.setVisible(False)
        self.main_layout.addWidget(self.filter_panel)

# table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Роль", "Название", "ИНН", "КПП", "Тип"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.doubleClicked.connect(self.edit_contagent)

        # context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

        self.table.keyPressEvent = self._table_key_press  # type: ignore[assignment]
        self.main_layout.addWidget(self.table)

    # data
    def load_data(self) -> None:
        self._fill_table(get_all_contagents())

    def _fill_table(self, conts) -> None:
        self.table.setRowCount(0)
        for row, c in enumerate(conts):
            self.table.insertRow(row)

            item_id = QTableWidgetItem(str(c.id))
            item_id.setData(Qt.ItemDataRole.UserRole, int(c.id))
            self.table.setItem(row, 0, item_id)

            role_text = "Покупатель" if c.role == "buyer" else ("Поставщик" if c.role == "supplier" else "Оба")
            org_text = "Юр. лицо" if c.organization_type == "company" else ("ИП" if c.organization_type == "ip" else "Физ. лицо")

            self.table.setItem(row, 1, QTableWidgetItem(role_text))
            self.table.setItem(row, 2, QTableWidgetItem(c.name))
            self.table.setItem(row, 3, QTableWidgetItem(c.inn or ""))
            self.table.setItem(row, 4, QTableWidgetItem(c.kpp or ""))
            self.table.setItem(row, 5, QTableWidgetItem(org_text))

    # selection
    def get_selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        v: Any = item.data(Qt.ItemDataRole.UserRole)
        try:
            return int(v)
        except Exception:
            return None

    def get_selected_ids(self) -> list[int]:
        rows = {it.row() for it in self.table.selectedItems()}
        out: list[int] = []
        for r in rows:
            item = self.table.item(r, 0)
            if not item:
                continue
            v: Any = item.data(Qt.ItemDataRole.UserRole)
            try:
                out.append(int(v))
            except Exception:
                pass
        return out

    # CRUD
    def add_contagent(self) -> None:
        from ui.contagent_form import ContagentForm
        dlg = ContagentForm(mode="create", on_saved=self._after_change, main_window=self.main_window)
        dlg.exec()

    def edit_contagent(self) -> None:
        cid = self.get_selected_id()
        if cid is None:
            self._msg("Выберите контрагента", "warning", 2500)
            return
        from ui.contagent_form import ContagentForm
        dlg = ContagentForm(contagent_id=cid, mode="edit", on_saved=self._after_change, main_window=self.main_window)
        dlg.exec()

    def copy_contagent(self) -> None:
        cid = self.get_selected_id()
        if cid is None:
            self._msg("Выберите контрагента", "warning", 2500)
            return
        from ui.contagent_form import ContagentForm
        dlg = ContagentForm(contagent_id=cid, mode="copy", on_saved=self._after_change, main_window=self.main_window)
        dlg.exec()

    def soft_delete_selected(self) -> None:
        ids = self.get_selected_ids()
        if not ids:
            self._msg("Выберите контрагентов", "warning", 2500)
            return

        reply = QMessageBox.question(
            self,
            "Перемещение в архив",
            f"Переместить в архив ({len(ids)})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for cid in ids:
            soft_delete_contagent(cid)

        self._after_change()
        self._msg(f"Перемещено в архив: {len(ids)}", "success", 3000)

    # search/filter
    def on_search(self, _text: str) -> None:
        # debounce 220ms
        self._search_timer.start(220)

    def _do_search(self) -> None:
        text = self.search_input.text().strip()
        self._fill_table(search_contagents(text))

    def toggle_filter(self) -> None:
        self.filter_panel.setVisible(not self.filter_panel.isVisible())

    def _on_filter_applied(self, filters: dict) -> None:
        from services.contagents import filter_contagents
        self._fill_table(filter_contagents(filters))

    def _on_filter_reset(self) -> None:
        self.load_data()

    def reset_filter(self) -> None:
        # совместимость (если где-то вызывается)
        self._on_filter_reset()

    # misc
    def _after_change(self) -> None:
        self.load_data()
        self.data_changed.emit()

    def _table_key_press(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete:
            self.soft_delete_selected()
        else:
            QTableWidget.keyPressEvent(self.table, event)

    def _open_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)

        a_add = menu.addAction("Создать")
        a_edit = menu.addAction("Редактировать")
        a_copy = menu.addAction("Копировать")
        menu.addSeparator()
        a_arch = menu.addAction("В архив")
        menu.addSeparator()
        a_refresh = menu.addAction("Обновить")

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen is None:
            return

        if chosen == a_add:
            self.add_contagent()
        elif chosen == a_edit:
            self.edit_contagent()
        elif chosen == a_copy:
            self.copy_contagent()
        elif chosen == a_arch:
            self.soft_delete_selected()
        elif chosen == a_refresh:
            self.load_data()
            self._msg("Обновлено", "success", 1500)
