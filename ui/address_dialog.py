from __future__ import annotations

import json
from typing import Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox
)


HOUSE_TYPES = ["Дом", "Корпус", "Строение", "Литер"]
FLAT_TYPES = ["Кв", "Секция", "Офис", "Помещение"]


def assemble_address(parts: dict[str, Any] | None) -> str:
    if not parts:
        return ""
    items: list[str] = []
    for key in ("country", "region", "city", "street"):
        v = (parts.get(key) or "").strip()
        if v:
            items.append(v)

    # house
    ht = (parts.get("house_type") or "").strip()
    hn = (parts.get("house_no") or "").strip()
    if hn:
        items.append(f"{ht} {hn}".strip())

    # flat
    ft = (parts.get("flat_type") or "").strip()
    fn = (parts.get("flat_no") or "").strip()
    if fn:
        items.append(f"{ft} {fn}".strip())

    return ", ".join([i for i in items if i]).strip()


class AddressDialog(QDialog):
    def __init__(self, title: str = "Адрес", initial_parts: dict[str, Any] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        self.parts: dict[str, Any] = dict(initial_parts or {})

        layout = QVBoxLayout(self)

        self.country = QLineEdit(self.parts.get("country", ""))
        self.region = QLineEdit(self.parts.get("region", ""))
        self.city = QLineEdit(self.parts.get("city", ""))
        self.street = QLineEdit(self.parts.get("street", ""))

        self.house_type = QComboBox()
        self.house_type.addItems(HOUSE_TYPES)
        if self.parts.get("house_type") in HOUSE_TYPES:
            self.house_type.setCurrentText(self.parts.get("house_type"))

        self.house_no = QLineEdit(self.parts.get("house_no", ""))

        self.flat_type = QComboBox()
        self.flat_type.addItems(FLAT_TYPES)
        if self.parts.get("flat_type") in FLAT_TYPES:
            self.flat_type.setCurrentText(self.parts.get("flat_type"))

        self.flat_no = QLineEdit(self.parts.get("flat_no", ""))

        def row(lbl: str, w):
            r = QHBoxLayout()
            r.addWidget(QLabel(lbl))
            r.addWidget(w)
            layout.addLayout(r)

        row("Страна", self.country)
        row("Регион", self.region)
        row("Город", self.city)
        row("Улица", self.street)

        r_house = QHBoxLayout()
        r_house.addWidget(QLabel("Дом"))
        r_house.addWidget(self.house_type)
        r_house.addWidget(self.house_no)
        layout.addLayout(r_house)

        r_flat = QHBoxLayout()
        r_flat.addWidget(QLabel("Кв/офис"))
        r_flat.addWidget(self.flat_type)
        r_flat.addWidget(self.flat_no)
        layout.addLayout(r_flat)

        self.preview = QLabel()
        self.preview.setWordWrap(True)
        layout.addWidget(QLabel("Собранный адрес"))
        layout.addWidget(self.preview)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.ok_btn.clicked.connect(self._on_ok)
        self.cancel_btn.clicked.connect(self.reject)

        for w in (self.country, self.region, self.city, self.street, self.house_no, self.flat_no):
            w.textChanged.connect(self._update_preview)
        self.house_type.currentIndexChanged.connect(self._update_preview)
        self.flat_type.currentIndexChanged.connect(self._update_preview)

        self._update_preview()

    def _collect(self) -> dict[str, Any]:
        return {
            "country": self.country.text().strip() or None,
            "region": self.region.text().strip() or None,
            "city": self.city.text().strip() or None,
            "street": self.street.text().strip() or None,
            "house_type": self.house_type.currentText().strip() or None,
            "house_no": self.house_no.text().strip() or None,
            "flat_type": self.flat_type.currentText().strip() or None,
            "flat_no": self.flat_no.text().strip() or None,
        }

    def _update_preview(self) -> None:
        parts = self._collect()
        self.preview.setText(assemble_address(parts))

    def _on_ok(self) -> None:
        self.parts = self._collect()
        self.accept()

    def get_parts(self) -> dict[str, Any]:
        return dict(self.parts)

    def get_json(self) -> str:
        return json.dumps(self.parts, ensure_ascii=False)
