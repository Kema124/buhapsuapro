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

        # filter widget
        self.filter_widget = QWidget()
        self.filter_layout = QVBoxLayout(self.filter_widget)

        self.f_name = QLineEdit(); self.f_name.setPlaceholderText("Название")
        self.f_inn = QLineEdit(); self.f_inn.setPlaceholderText("ИНН")

        self.f_role = QComboBox()
        self.f_role.addItem("Все", None)
        self.f_role.addItem("Покупатель", "buyer")
        self.f_role.addItem("Поставщик", "supplier")
        self.f_role.addItem("Оба", "both")

        self.f_org_type = QComboBox()
        self.f_org_type.addItem("Все", None)
        self.f_org_type.addItem("Юр. лицо", "company")
        self.f_org_type.addItem("ИП", "ip")
        self.f_org_type.addItem("Физ. лицо", "person")

        self.f_status = QComboBox()
        self.f_status.addItem("Все", None)
        self.f_status.addItem("Активные", True)
        self.f_status.addItem("Неактивные", False)

        apply_btn = QPushButton("Применить")
        reset_btn = QPushButton("Сбросить")
        apply_btn.clicked.connect(self.apply_filter)
        reset_btn.clicked.connect(self.reset_filter)

        for w in (self.f_name, self.f_inn, self.f_role, self.f_org_type, self.f_status, apply_btn, reset_btn):
            self.filter_layout.addWidget(w)

        self.filter_widget.setVisible(False)
        self.main_layout.addWidget(self.filter_widget)

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
        self.filter_widget.setVisible(not self.filter_widget.isVisible())

    def apply_filter(self) -> None:
        from services.contagents import filter_contagents
        filters = {
            "name": self.f_name.text().strip() or None,
            "inn": self.f_inn.text().strip() or None,
            "role": self.f_role.currentData(),
            "organization_type": self.f_org_type.currentData(),
            "is_active": self.f_status.currentData(),
        }
        self._fill_table(filter_contagents(filters))

    def reset_filter(self) -> None:
        self.f_name.clear()
        self.f_inn.clear()
        self.f_role.setCurrentIndex(0)
        self.f_org_type.setCurrentIndex(0)
        self.f_status.setCurrentIndex(0)
        self.load_data()

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
