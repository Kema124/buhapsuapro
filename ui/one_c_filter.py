from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout
)
from PySide6.QtCore import Signal


@dataclass(frozen=True)
class FilterField:
    key: str
    label: str
    kind: str = "text"  # "text" | "combo"
    placeholder: str = ""
    # for combo: list of (title, data)
    items: list[tuple[str, Any]] | None = None


class OneCFilterPanel(QWidget):
    """Единая панель фильтра (как в 1С): поля + Применить/Сбросить.

    Внешняя кнопка "Фильтр" управляет видимостью панели.
    """
    applied = Signal(dict)
    reset = Signal()

    def __init__(self, fields: list[FilterField]):
        super().__init__()
        self._fields = fields
        self._widgets: dict[str, QWidget] = {}

        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        root.addLayout(grid)

        row = 0
        col = 0

        for spec in self._fields:
            lbl = QLabel(spec.label)
            lbl.setObjectName("FilterLabel")

            if spec.kind == "combo":
                w = QComboBox()
                items = spec.items or []
                for title, data in items:
                    w.addItem(title, data)
            else:
                w = QLineEdit()
                if spec.placeholder:
                    w.setPlaceholderText(spec.placeholder)

            w.setObjectName("FilterField")
            self._widgets[spec.key] = w

            grid.addWidget(lbl, row, col * 2)
            grid.addWidget(w, row, col * 2 + 1)

            col += 1
            if col >= 2:
                col = 0
                row += 1

        btns = QHBoxLayout()
        btns.addStretch(1)

        self.btn_apply = QPushButton("Применить")
        self.btn_reset = QPushButton("Сбросить")
        self.btn_apply.setObjectName("FilterApply")
        self.btn_reset.setObjectName("FilterReset")

        btns.addWidget(self.btn_apply)
        btns.addWidget(self.btn_reset)
        root.addLayout(btns)

        self.btn_apply.clicked.connect(self._emit_applied)
        self.btn_reset.clicked.connect(self._do_reset)

    def values(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, w in self._widgets.items():
            if isinstance(w, QLineEdit):
                v = w.text().strip()
                out[k] = v or None
            elif isinstance(w, QComboBox):
                out[k] = w.currentData()
        return out

    def set_values(self, values: dict[str, Any]) -> None:
        for k, v in values.items():
            w = self._widgets.get(k)
            if w is None:
                continue
            if isinstance(w, QLineEdit):
                w.setText("" if v is None else str(v))
            elif isinstance(w, QComboBox):
                idx = w.findData(v)
                if idx >= 0:
                    w.setCurrentIndex(idx)

    def clear(self) -> None:
        for w in self._widgets.values():
            if isinstance(w, QLineEdit):
                w.clear()
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)

    def _emit_applied(self) -> None:
        self.applied.emit(self.values())

    def _do_reset(self) -> None:
        self.clear()
        self.reset.emit()
