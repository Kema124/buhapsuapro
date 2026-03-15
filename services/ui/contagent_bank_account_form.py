from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox
)

from services.banks import get_all_banks
from services.contagent_bank_accounts import create_bank_account, update_bank_account
from database.models import ContagentBankAccount


class ContagentBankAccountForm(QDialog):
    def __init__(
        self,
        contagent_id: int,
        account: ContagentBankAccount | None = None,
        parent: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Банковский счёт")
        self.setMinimumWidth(520)

        self.contagent_id = int(contagent_id)
        self.account = account

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Банк"))

        self.bank_combo = QComboBox()
        self._banks = get_all_banks()
        for b in self._banks:
            self.bank_combo.addItem(b.name, int(b.id))
        layout.addWidget(self.bank_combo)

        layout.addWidget(QLabel("Номер счёта"))
        self.acc_input = QLineEdit()
        self.acc_input.setMaxLength(34)
        layout.addWidget(self.acc_input)

        layout.addWidget(QLabel("Валюта (опционально)"))
        self.currency_input = QLineEdit()
        self.currency_input.setMaxLength(10)
        layout.addWidget(self.currency_input)

        layout.addWidget(QLabel("Примечание (опционально)"))
        self.note_input = QLineEdit()
        layout.addWidget(self.note_input)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.ok_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)

        if self.account is not None:
            self._load()

    def _load(self) -> None:
        account = self.account
        if account is None:
            return

        self.acc_input.setText(account.account_number or "")
        self.currency_input.setText(account.currency or "")
        self.note_input.setText(account.note or "")

        bank_id = getattr(account, "bank_id", None)
        if bank_id is not None:
            idx = self.bank_combo.findData(int(bank_id))
            if idx >= 0:
                self.bank_combo.setCurrentIndex(idx)

    def _save(self) -> None:
        bank_id = self.bank_combo.currentData()
        if bank_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите банк")
            return

        account_number = (self.acc_input.text() or "").strip()
        if not account_number:
            QMessageBox.warning(self, "Ошибка", "Введите номер счёта")
            return

        data = {
            "contagent_id": self.contagent_id,
            "bank_id": int(bank_id),
            "account_number": account_number,
            "currency": (self.currency_input.text() or "").strip() or None,
            "note": (self.note_input.text() or "").strip() or None,
        }

        try:
            if self.account is None:
                create_bank_account(data)
            else:
                account = self.account
                if account is None:
                    QMessageBox.warning(self, "Ошибка", "Счёт не найден")
                    return
                update_bank_account(int(account.id), data)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return

        self.accept()