
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QWidget


class BaseSectionWindow(QWidget):
    def __init__(self, *, main_window: Any | None = None) -> None:
        super().__init__()
        self.main_window = main_window

    def show_message(self, text: str, kind: str = 'info', timeout: int = 3000) -> None:
        if self.main_window and hasattr(self.main_window, 'show_message'):
            self.main_window.show_message(text, kind, timeout)
