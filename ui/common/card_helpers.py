from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QMessageBox, QWidget, QVBoxLayout,
    QLabel, QTabWidget, QLineEdit
)


def build_footer(parent: QWidget, *, on_save: Callable[[], None], on_ok: Callable[[], None], on_cancel: Callable[[], None], extra_buttons: list[QPushButton] | None = None) -> tuple[QHBoxLayout, QPushButton, QPushButton, QPushButton]:
    lay = QHBoxLayout()
    btn_save = QPushButton('Записать', parent)
    btn_ok = QPushButton('ОК', parent)
    btn_cancel = QPushButton('Отмена', parent)
    lay.addWidget(btn_save)
    lay.addWidget(btn_ok)
    if extra_buttons:
        for b in extra_buttons:
            lay.addWidget(b)
    lay.addStretch(1)
    lay.addWidget(btn_cancel)
    btn_save.clicked.connect(on_save)
    btn_ok.clicked.connect(on_ok)
    btn_cancel.clicked.connect(on_cancel)
    return lay, btn_save, btn_ok, btn_cancel


def build_card_shell(widget: QWidget, title: str, top_label: str, min_width: int = 640) -> tuple[QVBoxLayout, QLineEdit, QTabWidget]:
    widget.setWindowTitle(title)
    widget.setMinimumWidth(min_width)
    root = QVBoxLayout(widget)
    root.addWidget(QLabel(top_label))
    top_edit = QLineEdit(widget)
    root.addWidget(top_edit)
    tabs = QTabWidget(widget)
    root.addWidget(tabs, 1)
    return root, top_edit, tabs


def confirm_close_if_modified(parent: QWidget, is_modified: bool) -> bool:
    if not is_modified:
        return True
    res = QMessageBox.question(
        parent,
        'Несохраненные изменения',
        'Есть несохраненные изменения. Закрыть без сохранения?',
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return res == QMessageBox.StandardButton.Yes
