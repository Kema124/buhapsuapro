from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QApplication

from ui.assets import qss_icon_url
from ui.style_dark import DARK_QSS
from ui.style_light import LIGHT_QSS

ThemeCallback = Callable[[str], None]


class ThemeManager:
    """Глобальный менеджер темы.

    - apply(): применяет QSS на весь QApplication
    - toggle(): переключает
    - subscribe(): подписка на изменение темы (для перекраски иконок и т.п.)
    """

    _current: str = "light"
    _subscribers: set[ThemeCallback] = set()

    @classmethod
    def apply(cls, theme: str) -> None:
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            return

        cls._current = "dark" if theme == "dark" else "light"

        qss = DARK_QSS if cls._current == "dark" else LIGHT_QSS

        # подставляем пути к ассетам в QSS
        close_url = qss_icon_url("close.svg")
        qss = qss.replace("%CLOSE_SVG%", close_url)

        app.setStyleSheet(qss)

        for cb in list(cls._subscribers):
            try:
                cb(cls._current)
            except Exception:
                pass

    @classmethod
    def toggle(cls) -> None:
        cls.apply("dark" if cls._current != "dark" else "light")

    @classmethod
    def current(cls) -> str:
        return cls._current

    @classmethod
    def subscribe(cls, cb: ThemeCallback) -> None:
        cls._subscribers.add(cb)

    @classmethod
    def unsubscribe(cls, cb: ThemeCallback) -> None:
        cls._subscribers.discard(cb)
