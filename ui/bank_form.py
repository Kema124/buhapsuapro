from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox
)

from services.banks import get_bank_by_id, create_bank, update_bank


class BankForm(QDialog):
    def __init__(self, *, main_window=None, bank_id: int | None = None, mode: str = "create", on_saved=None):
        super().__init__()
        self.main_window = main_window
        self.bank_id = bank_id
        self.mode = mode
        self.on_saved = on_saved

        self.obj = None
        self.is_modified = False

        self.setWindowTitle("Банк")
        self.setFixedWidth(460)

        self._init_ui()
        if bank_id is not None:
            self._load()

    def _init_ui(self):
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Страна"))
        self.country = QComboBox()
        self.country.addItem("Россия", "RU")
        self.country.addItem("Абхазия", "ABH")
        lay.addWidget(self.country)

        lay.addWidget(QLabel("Наименование *"))
        self.name = QLineEdit()
        lay.addWidget(self.name)

        lay.addWidget(QLabel("БИК / Код"))
        self.bik = QLineEdit()
        lay.addWidget(self.bik)

        lay.addWidget(QLabel("Корр. счёт"))
        self.corr = QLineEdit()
        lay.addWidget(self.corr)

        lay.addWidget(QLabel("SWIFT"))
        self.swift = QLineEdit()
        lay.addWidget(self.swift)

        lay.addWidget(QLabel("Адрес"))
        self.address = QLineEdit()
        lay.addWidget(self.address)

        self.active = QCheckBox("Активен")
        self.active.setChecked(True)
        lay.addWidget(self.active)

        btns = QHBoxLayout()
        self.btn_save = QPushButton("Записать")
        self.btn_ok = QPushButton("ОК")
        self.btn_cancel = QPushButton("Отмена")
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        lay.addLayout(btns)

        self.btn_save.clicked.connect(self._save_only)
        self.btn_ok.clicked.connect(self._save_and_close)
        self.btn_cancel.clicked.connect(self.reject)

        for w in (self.name, self.bik, self.corr, self.swift, self.address):
            w.textChanged.connect(self._mark_modified)
        self.country.currentIndexChanged.connect(self._mark_modified)
        self.active.stateChanged.connect(self._mark_modified)

    def _mark_modified(self):
        self.is_modified = True

    def _load(self):
        self.obj = get_bank_by_id(self.bank_id) if self.bank_id is not None else None
        if not self.obj:
            return
        self.country.setCurrentIndex(self.country.findData(self.obj.country))
        self.name.setText(self.obj.name)
        self.bik.setText(self.obj.bik or "")
        self.corr.setText(self.obj.corr_account or "")
        self.swift.setText(self.obj.swift or "")
        self.address.setText(self.obj.address or "")
        self.active.setChecked(bool(self.obj.is_active))
        self.is_modified = False

        if self.mode == "copy":
            self.bank_id = None
            self.obj = None
            self.setWindowTitle("Копия: Банк")

    def _validate(self) -> bool:
        if not self.name.text().strip():
            if self.main_window:
                self.main_window.show_message("Наименование обязательно", "error", 4000)
            return False
        return True

    def _collect(self) -> dict[str, Any]:
        return {
            "country": self.country.currentData(),
            "name": self.name.text().strip(),
            "bik": self.bik.text().strip() or None,
            "corr_account": self.corr.text().strip() or None,
            "swift": self.swift.text().strip() or None,
            "address": self.address.text().strip() or None,
            "is_active": self.active.isChecked(),
        }

    def _save(self) -> bool:
        if not self.is_modified and self.mode != "create":
            return False
        if not self._validate():
            return False

        data = self._collect()

        try:
            if self.bank_id is None:
                self.bank_id = create_bank(data)
            else:
                update_bank(self.bank_id, data)
        except Exception as e:
            if self.main_window:
                self.main_window.show_message(str(e), "error", 7000)
            return False

        self.is_modified = False
        if self.on_saved:
            self.on_saved()
        return True

    def _save_only(self):
        if self._save() and self.main_window:
            self.main_window.show_message("Сохранено", "success", 2000)

    def _save_and_close(self):
        if self._save():
            self.accept()
