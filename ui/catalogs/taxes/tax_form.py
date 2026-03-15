from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox
)

from services.taxes import get_tax_by_id, create_tax, update_tax


class TaxForm(QDialog):
    def __init__(self, *, main_window=None, tax_id: int | None = None, mode: str = "create", on_saved=None):
        super().__init__()
        self.main_window = main_window
        self.tax_id = tax_id
        self.mode = mode
        self.on_saved = on_saved

        self.obj = None
        self.is_modified = False

        self.setWindowTitle("Налог/платёж")
        self.setFixedWidth(460)

        self._init_ui()
        if tax_id is not None:
            self._load()

    def _init_ui(self):
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Наименование *"))
        self.name = QLineEdit()
        lay.addWidget(self.name)

        lay.addWidget(QLabel("Вид платежа"))
        self.tax_type = QComboBox()
        self.tax_type.addItem("Налог", "tax")
        self.tax_type.addItem("Сбор", "fee")
        self.tax_type.addItem("Взнос", "contribution")
        self.tax_type.addItem("Пошлина", "duty")
        lay.addWidget(self.tax_type)

        lay.addWidget(QLabel("Ставка"))
        self.rate = QLineEdit()
        self.rate.setPlaceholderText("например: 10% или 1000")
        lay.addWidget(self.rate)

        lay.addWidget(QLabel("КБК"))
        self.kbk = QLineEdit()
        lay.addWidget(self.kbk)

        lay.addWidget(QLabel("Периодичность"))
        self.period = QComboBox()
        self.period.addItem("Не задано", None)
        self.period.addItem("Ежемесячно", "month")
        self.period.addItem("Ежеквартально", "quarter")
        self.period.addItem("Ежегодно", "year")
        self.period.addItem("Разово", "once")
        lay.addWidget(self.period)

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

        for w in (self.name, self.rate, self.kbk):
            w.textChanged.connect(self._mark_modified)
        self.tax_type.currentIndexChanged.connect(self._mark_modified)
        self.period.currentIndexChanged.connect(self._mark_modified)
        self.active.stateChanged.connect(self._mark_modified)

    def _mark_modified(self):
        self.is_modified = True

    def _load(self):
        self.obj = get_tax_by_id(self.tax_id) if self.tax_id is not None else None
        if not self.obj:
            return

        self.name.setText(self.obj.name)
        self.tax_type.setCurrentIndex(self.tax_type.findData(self.obj.tax_type))
        self.rate.setText(self.obj.rate or "")
        self.kbk.setText(self.obj.kbk or "")
        idx = self.period.findData(self.obj.periodicity)
        self.period.setCurrentIndex(idx if idx >= 0 else 0)
        self.active.setChecked(bool(self.obj.is_active))

        self.is_modified = False

        if self.mode == "copy":
            self.tax_id = None
            self.obj = None
            self.setWindowTitle("Копия: Налог/платёж")

    def _validate(self) -> bool:
        if not self.name.text().strip():
            if self.main_window:
                self.main_window.show_message("Наименование обязательно", "error", 4000)
            return False
        return True

    def _collect(self) -> dict[str, Any]:
        return {
            "name": self.name.text().strip(),
            "tax_type": self.tax_type.currentData(),
            "rate": self.rate.text().strip() or None,
            "kbk": self.kbk.text().strip() or None,
            "periodicity": self.period.currentData(),
            "is_active": self.active.isChecked(),
        }

    def _save(self) -> bool:
        if not self.is_modified and self.mode != "create":
            return False
        if not self._validate():
            return False

        data = self._collect()
        try:
            if self.tax_id is None:
                self.tax_id = create_tax(data)
            else:
                update_tax(self.tax_id, data)
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
