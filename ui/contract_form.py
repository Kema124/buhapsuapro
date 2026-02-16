from __future__ import annotations

from datetime import datetime, date

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QHBoxLayout, QPushButton, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate

from services.contagents import get_all_contagents
from services.contracts import (
    create_contract, update_contract, get_contract_by_id,
    STATUS_DRAFT, STATUS_ACTIVE, STATUS_CLOSED
)


STATUS_LABELS = {
    STATUS_DRAFT: "Черновик",
    STATUS_ACTIVE: "Активен",
    STATUS_CLOSED: "Закрыт",
}


class ContractForm(QDialog):
    def __init__(self, main_window=None, contract_id: int | None = None, mode: str = "create", on_saved=None):
        super().__init__()
        self.main_window = main_window
        self.contract_id = contract_id
        self.mode = mode  # create | edit | copy
        self.on_saved = on_saved

        self.is_modified = False
        self.contract = None

        self.setWindowTitle("Договор")
        self.setFixedWidth(480)

        self._init_ui()
        self._load_contagents()

        if self.contract_id is not None:
            self._load_data()

    def _msg(self, text: str, kind: str = "info", timeout: int = 4000) -> None:
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Контрагент
        layout.addWidget(QLabel("Контрагент *"))
        self.contagent = QComboBox()
        layout.addWidget(self.contagent)

        # Номер
        layout.addWidget(QLabel("Номер договора *"))
        self.number = QLineEdit()
        layout.addWidget(self.number)

        # Дата
        layout.addWidget(QLabel("Дата *"))
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        layout.addWidget(self.date)

        # Сумма
        layout.addWidget(QLabel("Сумма"))
        self.sum = QLineEdit()
        self.sum.setPlaceholderText("Например: 150000")
        layout.addWidget(self.sum)

        # Статус
        layout.addWidget(QLabel("Статус"))
        self.status = QComboBox()
        self.status.addItem(STATUS_LABELS[STATUS_DRAFT], STATUS_DRAFT)
        self.status.addItem(STATUS_LABELS[STATUS_ACTIVE], STATUS_ACTIVE)
        self.status.addItem(STATUS_LABELS[STATUS_CLOSED], STATUS_CLOSED)
        layout.addWidget(self.status)

        # Buttons
        btns = QHBoxLayout()
        self.btn_save = QPushButton("Записать")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Отмена")

        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        # Signals
        self.btn_save.clicked.connect(self._save_only)
        self.btn_ok.clicked.connect(self._save_and_close)
        self.btn_cancel.clicked.connect(self._close_form)

        for w in (self.contagent, self.number, self.date, self.sum, self.status):
            try:
                w.currentIndexChanged.connect(self._mark_modified)  # type: ignore[attr-defined]
            except Exception:
                pass
        self.number.textChanged.connect(self._mark_modified)
        self.sum.textChanged.connect(self._mark_modified)

    def _mark_modified(self) -> None:
        self.is_modified = True

    def _load_contagents(self) -> None:
        self.contagent.clear()
        for c in get_all_contagents():
            self.contagent.addItem(c.name, int(c.id))

    def _load_data(self) -> None:
        c = get_contract_by_id(int(self.contract_id))
        if not c:
            self._msg("Договор не найден", "error", 6000)
            return

        self.contract = c

        # режим copy: id не сохраняем, но поля копируем
        if self.mode == "copy":
            self.contract_id = None
            self.setWindowTitle("Копия договора")

        self.number.setText(c.number)
        if c.date is not None:
            self.date.setDate(QDate(c.date.year, c.date.month, c.date.day))
        else:
            self.date.setDate(QDate.currentDate())
        self.sum.setText("" if c.sum is None else str(c.sum))

        idx = self.status.findData(c.status)
        if idx >= 0:
            self.status.setCurrentIndex(idx)

        # контрагент
        cidx = self.contagent.findData(int(c.contagent_id))
        if cidx >= 0:
            self.contagent.setCurrentIndex(cidx)

        self.is_modified = False

    def _validate(self) -> bool:
        if self.contagent.currentData() is None:
            self._msg("Выберите контрагента", "warning", 3000)
            return False

        if not self.number.text().strip():
            self._msg("Номер договора обязателен", "warning", 3000)
            return False

        # сумма — необязательна, но если ввели, должна быть числом
        s = self.sum.text().strip()
        if s and not s.isdigit():
            self._msg("Сумма должна быть числом", "warning", 3500)
            return False

        return True

    def _collect(self) -> dict:
        return {
            "contagent_id": int(self.contagent.currentData()),
            "number": self.number.text().strip(),
            "date": self.date.date().toPython(),
            "sum": int(self.sum.text().strip()) if self.sum.text().strip().isdigit() else None,
            "status": str(self.status.currentData()),
        }

    def _save(self) -> bool:
        if not self.is_modified and self.mode != "copy":
            return False

        if not self._validate():
            return False

        data = self._collect()

        try:
            if self.contract_id is None:
                new_id = create_contract(data)
                self.contract_id = new_id
            else:
                update_contract(int(self.contract_id), data)
        except Exception as e:
            self._msg(str(e), "error", 7000)
            return False

        self.is_modified = False
        if self.on_saved:
            self.on_saved()
        return True

    def _save_only(self) -> None:
        if self._save():
            self._msg("Договор сохранён", "success", 2500)

    def _save_and_close(self) -> None:
        if self._save():
            self.accept()

    def _close_form(self) -> None:
        if self.is_modified:
            ans = QMessageBox.question(
                self,
                "Несохранённые данные",
                "Есть несохранённые изменения. Закрыть форму?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
        self.reject()
