from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QPoint, QTimer

from services.contracts import (
    get_all_contracts, search_contracts, soft_delete_contract
)
from ui.contract_form import ContractForm


@dataclass(frozen=True)
class DocSection:
    title: str
    key: str
    can_post: bool


DOC_SECTIONS: list[DocSection] = [
    DocSection("Договоры", "contracts", False),  # НЕ проводим
    DocSection("Акты (входящие)", "acts_in", True),
    DocSection("Акты (исходящие)", "acts_out", True),
    DocSection("Счета (входящие)", "invoices_in", True),
    DocSection("Счета (исходящие)", "invoices_out", True),
    DocSection("Смета", "estimate", False),
    DocSection("Кассовые документы", "cash", True),
    DocSection("Банковские документы", "bank", True),
    DocSection("ОС и НМА", "assets", True),
    DocSection("Зарплата", "payroll", True),
]


STATUS_LABELS = {
    "draft": "Черновик",
    "active": "Активен",
    "closed": "Закрыт",
}


class DocumentsWindow(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Документы")
        self._init_ui()

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._reload_current)

        self.load_data()

    def _msg(self, text: str, kind: str = "info", timeout: int = 3000) -> None:
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def _init_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        self.nav = QListWidget()
        self.nav.setFixedWidth(300)
        self.nav.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        root.addWidget(self.nav)

        right = QVBoxLayout()
        right.setSpacing(10)
        root.addLayout(right, 1)

        top = QHBoxLayout()
        top.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск (для договоров уже гибкий)")
        self.search.textChanged.connect(self._on_search_changed)
        top.addWidget(self.search, 1)

        self.btn_add = QPushButton("Создать")
        self.btn_open = QPushButton("Открыть")
        self.btn_copy = QPushButton("Копировать")
        self.btn_archive = QPushButton("В архив")
        self.btn_post = QPushButton("Провести")
        self.btn_unpost = QPushButton("Отменить")
        self.btn_refresh = QPushButton("Обновить")

        for b in (self.btn_add, self.btn_open, self.btn_copy, self.btn_archive, self.btn_post, self.btn_unpost, self.btn_refresh):
            top.addWidget(b)

        right.addLayout(top)

        self.stack = QStackedWidget()
        right.addWidget(self.stack, 1)

        self._tables: dict[str, QTableWidget] = {}
        self._can_post: dict[str, bool] = {}

        for s in DOC_SECTIONS:
            item = QListWidgetItem(s.title)
            item.setData(Qt.ItemDataRole.UserRole, s.key)
            self.nav.addItem(item)

            page, table = self._make_list_page()
            self.stack.addWidget(page)
            self._tables[s.key] = table
            self._can_post[s.key] = s.can_post

        self.nav.currentRowChanged.connect(self._section_changed)
        self.nav.setCurrentRow(0)

        # buttons
        self.btn_add.clicked.connect(self._create)
        self.btn_open.clicked.connect(self._open)
        self.btn_copy.clicked.connect(self._copy)
        self.btn_archive.clicked.connect(self._archive)
        self.btn_post.clicked.connect(lambda: self._msg("Проведение — позже (для актов/счетов/кассы/банка)", "info", 4000))
        self.btn_unpost.clicked.connect(lambda: self._msg("Отмена проведения — позже", "info", 4000))
        self.btn_refresh.clicked.connect(self.load_data)

    def _make_list_page(self) -> tuple[QWidget, QTableWidget]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["ID", "Номер", "Дата", "Контрагент", "Сумма", "Статус"])
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)

        table.doubleClicked.connect(self._open)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda p, t=table: self._menu(t, p))

        layout.addWidget(table)
        return page, table

    def current_key(self) -> str:
        item = self.nav.currentItem()
        if not item:
            return "contracts"
        key: Any = item.data(Qt.ItemDataRole.UserRole)
        return str(key) if key else "contracts"

    def current_table(self) -> QTableWidget | None:
        return self._tables.get(self.current_key())

    def _section_changed(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        self._update_post_buttons()
        self.load_data()

    def _update_post_buttons(self) -> None:
        can_post = bool(self._can_post.get(self.current_key(), False))
        self.btn_post.setVisible(can_post)
        self.btn_unpost.setVisible(can_post)

    def _on_search_changed(self, _text: str) -> None:
        self._search_timer.start(220)

    def _reload_current(self) -> None:
        self.load_data()

    def load_data(self) -> None:
        key = self.current_key()

        if key == "contracts":
            self._load_contracts()
            return

        # остальные пока заглушки
        table = self.current_table()
        if not table:
            return
        table.setRowCount(0)
        self._msg("Этот вид документов будет реализован на следующем этапе", "info", 2500)

    def _load_contracts(self) -> None:
        table = self.current_table()
        if not table:
            return

        q = self.search.text().strip()
        contracts = search_contracts(q) if q else get_all_contracts()

        table.setRowCount(0)
        for r, c in enumerate(contracts):
            table.insertRow(r)

            it_id = QTableWidgetItem(str(c.id))
            it_id.setData(Qt.ItemDataRole.UserRole, int(c.id))
            table.setItem(r, 0, it_id)

            table.setItem(r, 1, QTableWidgetItem(c.number))
            table.setItem(r, 2, QTableWidgetItem(str(c.date)))
            table.setItem(r, 3, QTableWidgetItem(c.contagent.name if c.contagent else ""))
            table.setItem(r, 4, QTableWidgetItem("" if c.sum is None else str(c.sum)))
            table.setItem(r, 5, QTableWidgetItem(STATUS_LABELS.get(c.status, c.status)))

    def selected_ids(self) -> list[int]:
        table = self.current_table()
        if not table:
            return []
        rows = {it.row() for it in table.selectedItems()}
        ids: list[int] = []
        for r in rows:
            item = table.item(r, 0)
            if not item:
                continue
            v: Any = item.data(Qt.ItemDataRole.UserRole)
            try:
                ids.append(int(v))
            except Exception:
                pass
        return ids

    # ---------------- actions (для договоров реально работают)
    def _create(self) -> None:
        if self.current_key() != "contracts":
            self._msg("Создание будет доступно после реализации этого вида документов", "info", 3500)
            return
        dlg = ContractForm(main_window=self.main_window, mode="create", on_saved=self.load_data)
        dlg.exec()

    def _open(self) -> None:
        if self.current_key() != "contracts":
            self._msg("Открытие будет доступно после реализации этого вида документов", "info", 3500)
            return
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите договор", "warning", 2500)
            return
        dlg = ContractForm(main_window=self.main_window, contract_id=ids[0], mode="edit", on_saved=self.load_data)
        dlg.exec()

    def _copy(self) -> None:
        if self.current_key() != "contracts":
            self._msg("Копирование будет доступно после реализации этого вида документов", "info", 3500)
            return
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите договор", "warning", 2500)
            return
        dlg = ContractForm(main_window=self.main_window, contract_id=ids[0], mode="copy", on_saved=self.load_data)
        dlg.exec()

    def _archive(self) -> None:
        if self.current_key() != "contracts":
            self._msg("Архив будет доступен после реализации этого вида документов", "info", 3500)
            return
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите договор(ы)", "warning", 2500)
            return

        ans = QMessageBox.question(
            self,
            "В архив",
            f"Переместить в архив ({len(ids)})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans != QMessageBox.StandardButton.Yes:
            return

        ok = 0
        for cid in ids:
            try:
                soft_delete_contract(cid)
                ok += 1
            except Exception as e:
                self._msg(f"Не удалось архивировать {cid}: {e}", "error", 6000)

        self.load_data()
        self._msg(f"Перемещено в архив: {ok}", "success", 3000)

    # ---------------- context menu
    def _menu(self, table: QTableWidget, pos: QPoint) -> None:
        menu = QMenu(self)
        a_add = menu.addAction("Создать")
        a_open = menu.addAction("Открыть")
        a_copy = menu.addAction("Копировать")
        menu.addSeparator()
        a_arch = menu.addAction("В архив")
        menu.addSeparator()
        a_refresh = menu.addAction("Обновить")

        chosen = menu.exec(table.viewport().mapToGlobal(pos))
        if not chosen:
            return
        if chosen == a_add:
            self._create()
        elif chosen == a_open:
            self._open()
        elif chosen == a_copy:
            self._copy()
        elif chosen == a_arch:
            self._archive()
        elif chosen == a_refresh:
            self.load_data()
            self._msg("Обновлено", "success", 1500)
