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

from services.invoices import (
    get_invoices, search_invoices
)
from ui.invoice_form import InvoiceForm

from services.bank_receipts import (
    get_bank_receipts,
    search_bank_receipts,
    archive_bank_receipts,
    post_bank_receipt,
    unpost_bank_receipt,
)
from ui.bank_receipt_form import BankReceiptForm


@dataclass(frozen=True)
class DocSection:
    title: str
    key: str
    can_post: bool


DOC_SECTIONS: list[DocSection] = [
    DocSection("Акты (входящие)", "acts_in", True),
    DocSection("Акты (исходящие)", "acts_out", True),
    DocSection("Счета на оплату покупателям", "invoices_out", False),
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
    "posted": "Проведен",
    "canceled": "Отменен",
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
        self.search.setPlaceholderText("Поиск")
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
        self.btn_post.clicked.connect(self._post)
        self.btn_unpost.clicked.connect(self._unpost)
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
            return "invoices_out"
        key: Any = item.data(Qt.ItemDataRole.UserRole)
        return str(key) if key else "invoices_out"

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

        if key == "invoices_out":
            self._load_invoices(direction="out")
            return

        if key == "bank":
            self._load_bank_receipts()
            return

        # остальные пока заглушки
        table = self.current_table()
        if not table:
            return
        table.setRowCount(0)
        self._msg("Этот вид документов будет реализован на следующем этапе", "info", 2500)

    def _load_bank_receipts(self) -> None:
        table = self.current_table()
        if not table:
            return

        q = self.search.text().strip()
        docs = search_bank_receipts(q) if q else get_bank_receipts()

        table.setRowCount(0)
        for r, d in enumerate(docs):
            table.insertRow(r)

            it_id = QTableWidgetItem(str(d.id))
            it_id.setData(Qt.ItemDataRole.UserRole, int(d.id))
            table.setItem(r, 0, it_id)
            table.setItem(r, 1, QTableWidgetItem(d.number))
            table.setItem(r, 2, QTableWidgetItem(str(d.date)))
            cont_name = ""
            try:
                cont_name = d.contagent.name if d.contagent else ""
            except Exception:
                cont_name = ""
            table.setItem(r, 3, QTableWidgetItem(cont_name))
            table.setItem(r, 4, QTableWidgetItem(str(d.amount)))
            status_label = STATUS_LABELS.get(getattr(d, "status", "draft"), getattr(d, "status", "")) or ""
            table.setItem(r, 5, QTableWidgetItem(str(status_label)))

    def _load_invoices(self, direction: str) -> None:
        table = self.current_table()
        if not table:
            return

        q = self.search.text().strip()
        invoices = search_invoices(direction, q) if q else get_invoices(direction)

        table.setRowCount(0)
        for r, inv in enumerate(invoices):
            table.insertRow(r)

            it_id = QTableWidgetItem(str(inv.id))
            it_id.setData(Qt.ItemDataRole.UserRole, int(inv.id))
            table.setItem(r, 0, it_id)

            table.setItem(r, 1, QTableWidgetItem(inv.number))
            table.setItem(r, 2, QTableWidgetItem(str(inv.date)))
            # контрагент — из договора
            cont_name = ""
            try:
                cont_name = inv.contract.contagent.name if inv.contract and inv.contract.contagent else ""
            except Exception:
                cont_name = ""
            table.setItem(r, 3, QTableWidgetItem(cont_name))
            table.setItem(r, 4, QTableWidgetItem(str(inv.sum)))
            status_label = STATUS_LABELS.get(getattr(inv, "status", "draft"), getattr(inv, "status", "")) or ""
            table.setItem(r, 5, QTableWidgetItem(str(status_label)))

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
        key = self.current_key()

        if key == "invoices_out":
            dlg = InvoiceForm(main_window=self.main_window, direction="out", mode="create", on_saved=self.load_data)
            dlg.exec()
            return

        if key == "bank":
            dlg = BankReceiptForm(main_window=self.main_window, mode="create", on_saved=self.load_data)
            dlg.exec()
            return

        self._msg("Создание будет доступно после реализации этого вида документов", "info", 3500)

    def _open(self) -> None:
        key = self.current_key()
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите документ", "warning", 2500)
            return

        if key == "invoices_out":
            dlg = InvoiceForm(main_window=self.main_window, invoice_id=ids[0], direction="out", mode="edit", on_saved=self.load_data)
            dlg.exec()
            return

        if key == "bank":
            dlg = BankReceiptForm(main_window=self.main_window, receipt_id=ids[0], mode="edit", on_saved=self.load_data)
            dlg.exec()
            return

        self._msg("Открытие будет доступно после реализации этого вида документов", "info", 3500)

    def _copy(self) -> None:
        key = self.current_key()
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите документ", "warning", 2500)
            return

        if key == "invoices_out":
            dlg = InvoiceForm(main_window=self.main_window, invoice_id=ids[0], direction="out", mode="copy", on_saved=self.load_data)
            dlg.exec()
            return

        if key == "bank":
            dlg = BankReceiptForm(main_window=self.main_window, receipt_id=ids[0], mode="copy", on_saved=self.load_data)
            dlg.exec()
            return

        self._msg("Копирование будет доступно после реализации этого вида документов", "info", 3500)

    def _archive(self) -> None:
        key = self.current_key()
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите документ(ы)", "warning", 2500)
            return

        if key == "bank":
            try:
                n = archive_bank_receipts(ids)
            except Exception as e:
                self._msg(f"Ошибка архивации: {e}", "error", 6000)
                return
            self._msg(f"Перемещено в архив: {n}", "success", 2500)
            self.load_data()
            return

        self._msg("Архив для этого документа будет на следующем этапе", "info", 3500)

    def _post(self) -> None:
        key = self.current_key()
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите документ", "warning", 2500)
            return

        if key == "bank":
            try:
                post_bank_receipt(ids[0])
            except Exception as e:
                self._msg(f"Ошибка проведения: {e}", "error", 7000)
                return
            self._msg("Документ проведен", "success", 2000)
            self.load_data()
            return

        self._msg("Проведение документов будет реализовано на следующем этапе", "info", 4000)
    def _unpost(self) -> None:
        key = self.current_key()
        ids = self.selected_ids()
        if not ids:
            self._msg("Выберите документ", "warning", 2500)
            return

        if key == "bank":
            try:
                unpost_bank_receipt(ids[0])
            except Exception as e:
                self._msg(f"Ошибка отмены: {e}", "error", 7000)
                return
            self._msg("Проведение отменено", "success", 2000)
            self.load_data()
            return

        self._msg("Отмена проведения будет реализована на следующем этапе", "info", 4000)
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