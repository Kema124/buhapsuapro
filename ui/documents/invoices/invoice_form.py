from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QHBoxLayout, QPushButton
)
from PySide6.QtCore import QDate

from typing import Any

from services.contracts import get_all_contracts
from services.invoices import (
    create_invoice, update_invoice, get_invoice_by_id,
    STATUS_DRAFT, STATUS_CANCELED,
)


STATUS_LABELS = {
    STATUS_DRAFT: "Черновик",
    STATUS_CANCELED: "Отменен",
}


class InvoiceForm(QDialog):
    def __init__(
        self,
        main_window=None,
        invoice_id: int | None = None,
        direction: str = "out",
        mode: str = "create",
        on_saved=None,
    ):
        super().__init__()
        self.main_window = main_window
        self.invoice_id = invoice_id
        self.direction = direction
        self.mode = mode
        self.on_saved = on_saved

        self.is_modified = False
        self.invoice = None

        self.setWindowTitle("Счет на оплату")
        self.setFixedWidth(520)

        self._init_ui()
        self._load_contracts()

        if self.invoice_id is not None:
            self._load_data()

    def _msg(self, text: str, kind: str = "info", timeout: int = 4000) -> None:
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def _safe_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Договор *"))
        self.contract = QComboBox()
        layout.addWidget(self.contract)

        layout.addWidget(QLabel("Номер счета *"))
        self.number = QLineEdit()
        layout.addWidget(self.number)

        layout.addWidget(QLabel("Дата *"))
        from PySide6.QtWidgets import QDateEdit

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        layout.addWidget(self.date)

        layout.addWidget(QLabel("Сумма *"))
        self.sum = QLineEdit()
        self.sum.setPlaceholderText("Например: 150000")
        layout.addWidget(self.sum)


        layout.addWidget(QLabel("Статус"))
        self.status = QComboBox()
        for k, v in STATUS_LABELS.items():
            self.status.addItem(v, k)
        layout.addWidget(self.status)

        btns = QHBoxLayout()
        self.btn_save = QPushButton("Записать")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Отмена")
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.btn_save.clicked.connect(self._save_only)
        self.btn_ok.clicked.connect(self._save_and_close)
        self.btn_cancel.clicked.connect(self.close)

        self.number.textChanged.connect(self._mark_modified)
        self.sum.textChanged.connect(self._mark_modified)
        self.contract.currentIndexChanged.connect(self._mark_modified)
        self.status.currentIndexChanged.connect(self._mark_modified)

    def _mark_modified(self) -> None:
        self.is_modified = True

    def _load_contracts(self) -> None:
        self.contract.clear()
        for c in get_all_contracts():
            cid = self._safe_int(getattr(c, "id", None))
            if cid is not None:
                label = f"{c.number} от {c.date}"
                self.contract.addItem(label, cid)

    def _load_data(self) -> None:
        if self.invoice_id is None:
            return
        inv = get_invoice_by_id(self.invoice_id)
        if not inv:
            self._msg("Счет не найден", "error", 6000)
            return
        self.invoice = inv

        if self.mode == "copy":
            self.invoice_id = None
            self.setWindowTitle("Копия счета на оплату")

        self.direction = getattr(inv, "direction", self.direction) or self.direction
        self.number.setText(inv.number)
        if inv.date:
            self.date.setDate(QDate(inv.date.year, inv.date.month, inv.date.day))

        self.sum.setText(str(inv.sum))

        cidx = self.contract.findData(self._safe_int(getattr(inv, "contract_id", None)))
        if cidx >= 0:
            self.contract.setCurrentIndex(cidx)



        sidx = self.status.findData(getattr(inv, "status", STATUS_DRAFT))
        if sidx >= 0:
            self.status.setCurrentIndex(sidx)

        self.is_modified = False

    def _validate(self) -> bool:
        if self.contract.currentData() is None:
            self._msg("Выберите договор", "warning", 3500)
            return False
        if not self.number.text().strip():
            self._msg("Номер счета обязателен", "warning", 3500)
            return False
        s = self.sum.text().strip()
        if not s.isdigit() or int(s) <= 0:
            self._msg("Сумма должна быть положительным числом", "warning", 3500)
            return False
        return True

    def _collect(self) -> dict:
        return {
            "contract_id": int(self.contract.currentData()),
            "direction": str(self.direction),
            "number": self.number.text().strip(),
            "date": self.date.date().toPython(),
            "sum": int(self.sum.text()),
            "status": str(self.status.currentData()),
        }

    def _save(self) -> bool:
        if not self.is_modified and self.mode != "copy":
            return False
        if not self._validate():
            return False

        data = self._collect()
        try:
            if self.invoice_id is None:
                self.invoice_id = create_invoice(data)
            else:
                update_invoice(self.invoice_id, data)
        except Exception as e:
            self._msg(f"Ошибка сохранения: {e}", "error", 6000)
            return False

        self.is_modified = False
        if self.on_saved:
            self.on_saved()
        return True

    def _save_only(self) -> None:
        self._save()

    def _save_and_close(self) -> None:
        if self._save():
            self.accept()