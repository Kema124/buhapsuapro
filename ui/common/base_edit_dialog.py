
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton


class BaseEditDialog(QDialog):
    """Общая база для карточек редактирования.

    Ничего не навязывает по layout, но даёт единые кнопки и служебные helpers.
    """

    def __init__(self, *, main_window: Any | None = None) -> None:
        super().__init__()
        self.main_window = main_window
        self.is_modified = False

    def create_standard_buttons(self) -> tuple[QHBoxLayout, QPushButton, QPushButton, QPushButton]:
        row = QHBoxLayout()
        btn_save = QPushButton('Записать')
        btn_ok = QPushButton('OK')
        btn_cancel = QPushButton('Отмена')
        row.addWidget(btn_save)
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        row.addStretch(1)
        return row, btn_save, btn_ok, btn_cancel

    def mark_modified(self, *_args: Any) -> None:
        self.is_modified = True

    def show_message(self, text: str, kind: str = 'info', timeout: int = 4000) -> None:
        if self.main_window and hasattr(self.main_window, 'show_message'):
            self.main_window.show_message(text, kind, timeout)
