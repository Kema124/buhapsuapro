from __future__ import annotations

from PySide6.QtWidgets import QApplication
from ui.style_light import LIGHT_QSS
from ui.style_dark import DARK_QSS


class ThemeManager:
    _current = "light"

    @classmethod
    def apply(cls, theme: str) -> None:
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            return

        cls._current = "dark" if theme == "dark" else "light"
        app.setStyleSheet(DARK_QSS if cls._current == "dark" else LIGHT_QSS)

    @classmethod
    def toggle(cls) -> None:
        cls.apply("dark" if cls._current != "dark" else "light")

    @classmethod
    def current(cls) -> str:
        return cls._current
