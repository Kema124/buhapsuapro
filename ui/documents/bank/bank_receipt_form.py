from __future__ import annotations

from decimal import Decimal
from typing import Any

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from services.bank_receipts import (
    create_bank_receipt,
    get_bank_receipt_by_id,
    post_bank_receipt,
    unpost_bank_receipt,
    update_bank_receipt,
)
from services.contagents import get_all_contagents
from services.contracts import get_contracts_by_contagent


STATUS_LABELS = {
    "draft": "Черновик",
    "posted": "Проведен",
    "canceled": "Отменен",
}


class BankReceiptForm(QDialog):
    """Документ: Поступление денежных средств (Банк)."""

    def __init__(
        self,
        main_window=None,
        receipt_id: int | None = None,
        mode: str = "create",  # create|edit|copy
        on_saved=None,
    ):
        super().__init__()
        self.main_window = main_window
        self.receipt_id = receipt_id
        self.mode = mode
        self.on_saved = on_saved

        self.is_modified = False
        self.receipt = None

        self.setWindowTitle("Поступление денежных средств (Банк)")
        self.setFixedWidth(720)

        self._init_ui()
        self._load_contagents()

        if self.receipt_id is not None:
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

        # header
        layout.addWidget(QLabel("Номер *"))
        self.number = QLineEdit()
        self.number.setPlaceholderText("Например: ПД-000001")
        layout.addWidget(self.number)

        layout.addWidget(QLabel("Дата *"))
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        layout.addWidget(self.date)

        # contagent + contract
        layout.addWidget(QLabel("Плательщик (контрагент)"))
        self.contagent = QComboBox()
        self.contagent.currentIndexChanged.connect(self._load_contracts)
        layout.addWidget(self.contagent)

        layout.addWidget(QLabel("Договор"))
        self.contract = QComboBox()
        layout.addWidget(self.contract)

        layout.addWidget(QLabel("Сумма *"))
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Например: 150000.00")
        layout.addWidget(self.amount)

        layout.addWidget(QLabel("Назначение платежа"))
        self.purpose = QLineEdit()
        layout.addWidget(self.purpose)

        layout.addWidget(QLabel("Наш счёт (опционально)"))
        self.our_account = QLineEdit()
        self.our_account.setPlaceholderText("Номер расчетного счета")
        layout.addWidget(self.our_account)

        layout.addWidget(QLabel("Счет плательщика (опционально)"))
        self.payer_account = QLineEdit()
        self.payer_account.setPlaceholderText("Номер счета плательщика")
        layout.addWidget(self.payer_account)

        layout.addWidget(QLabel("Статус"))
        self.status = QComboBox()
        for k, v in STATUS_LABELS.items():
            self.status.addItem(v, k)
        layout.addWidget(self.status)

        # actions
        btns = QHBoxLayout()
        self.btn_save = QPushButton("Записать")
        self.btn_post = QPushButton("Провести")
        self.btn_unpost = QPushButton("Отменить")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Отмена")

        for b in (self.btn_save, self.btn_post, self.btn_unpost, self.btn_ok, self.btn_cancel):
            btns.addWidget(b)
        layout.addLayout(btns)

        self.btn_save.clicked.connect(self._save_only)
        self.btn_ok.clicked.connect(self._save_and_close)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_post.clicked.connect(self._post)
        self.btn_unpost.clicked.connect(self._unpost)

        for w in (self.number, self.amount, self.purpose, self.our_account, self.payer_account):
            w.textChanged.connect(self._mark_modified)
        self.date.dateChanged.connect(self._mark_modified)
        self.contagent.currentIndexChanged.connect(self._mark_modified)
        self.contract.currentIndexChanged.connect(self._mark_modified)
        self.status.currentIndexChanged.connect(self._mark_modified)

    def _mark_modified(self) -> None:
        self.is_modified = True

    def _load_contagents(self) -> None:
        self.contagent.clear()
        self.contagent.addItem("— не выбран —", None)
        for c in get_all_contagents():
            cid = self._safe_int(getattr(c, "id", None))
            if cid is not None:
                self.contagent.addItem(c.name, cid)
        self._load_contracts()

    def _load_contracts(self) -> None:
        self.contract.clear()
        self.contract.addItem("— не выбран —", None)
        cid = self.contagent.currentData()
        if cid is None:
            return
        for ctr in get_contracts_by_contagent(int(cid)):
            self.contract.addItem(f"{ctr.number} от {ctr.date}", int(ctr.id))

    def _set_readonly_posted(self, posted: bool) -> None:
        for w in (self.number, self.amount, self.purpose, self.our_account, self.payer_account):
            w.setReadOnly(posted)
        self.date.setEnabled(not posted)
        self.contagent.setEnabled(not posted)
        self.contract.setEnabled(not posted)
        self.btn_post.setEnabled(not posted)
        self.btn_unpost.setEnabled(posted)

    def _load_data(self) -> None:
        if self.receipt_id is None:
            return
        r = get_bank_receipt_by_id(self.receipt_id)
        if not r:
            self._msg("Документ не найден", "error", 6000)
            return
        self.receipt = r

        if self.mode == "copy":
            self.receipt_id = None
            self.setWindowTitle("Копия: Поступление денежных средств (Банк)")

        self.number.setText(r.number)
        if r.date:
            self.date.setDate(QDate(r.date.year, r.date.month, r.date.day))

        # contagent + contract
        cidx = self.contagent.findData(self._safe_int(getattr(r, "contagent_id", None)))
        if cidx >= 0:
            self.contagent.setCurrentIndex(cidx)
        self._load_contracts()
        kidx = self.contract.findData(self._safe_int(getattr(r, "contract_id", None)))
        if kidx >= 0:
            self.contract.setCurrentIndex(kidx)

        self.amount.setText(str(r.amount))
        self.purpose.setText(r.purpose or "")
        self.our_account.setText(r.our_account or "")
        self.payer_account.setText(r.payer_account or "")

        sidx = self.status.findData(getattr(r, "status", "draft"))
        if sidx >= 0:
            self.status.setCurrentIndex(sidx)

        self._set_readonly_posted(getattr(r, "status", "draft") == "posted")
        self.is_modified = False

    def _validate(self) -> bool:
        if not self.number.text().strip():
            self._msg("Номер обязателен", "warning", 3500)
            return False
        s = self.amount.text().strip().replace(",", ".")
        try:
            v = Decimal(s)
        except Exception:
            self._msg("Сумма должна быть числом", "warning", 3500)
            return False
        if v <= 0:
            self._msg("Сумма должна быть > 0", "warning", 3500)
            return False
        return True

    def _collect(self) -> dict:
        amt = Decimal(self.amount.text().strip().replace(",", "."))
        return {
            "number": self.number.text().strip(),
            "date": self.date.date().toPython(),
            "contagent_id": self._safe_int(self.contagent.currentData()),
            "contract_id": self._safe_int(self.contract.currentData()),
            "amount": amt,
            "purpose": self.purpose.text().strip() or None,
            "our_account": self.our_account.text().strip() or None,
            "payer_account": self.payer_account.text().strip() or None,
            "status": str(self.status.currentData() or "draft"),
        }

    def _save(self) -> bool:
        if self.mode != "copy" and not self.is_modified:
            return False
        if not self._validate():
            return False
        data = self._collect()
        try:
            if self.receipt_id is None:
                self.receipt_id = create_bank_receipt(data)
            else:
                update_bank_receipt(self.receipt_id, data)
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

    def _post(self) -> None:
        if self.receipt_id is None:
            if not self._save():
                return
        try:
            post_bank_receipt(int(self.receipt_id))
        except Exception as e:
            self._msg(f"Ошибка проведения: {e}", "error", 7000)
            return
        self._msg("Документ проведен", "success", 2500)
        self._load_data()
        if self.on_saved:
            self.on_saved()

    def _unpost(self) -> None:
        if self.receipt_id is None:
            return
        try:
            unpost_bank_receipt(int(self.receipt_id))
        except Exception as e:
            self._msg(f"Ошибка отмены проведения: {e}", "error", 7000)
            return
        self._msg("Проведение отменено", "success", 2500)
        self._load_data()
        if self.on_saved:
            self.on_saved()
