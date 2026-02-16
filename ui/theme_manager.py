from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QApplication

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
        app.setStyleSheet(DARK_QSS if cls._current == "dark" else LIGHT_QSS)

        # уведомим подписчиков
        for cb in list(cls._subscribers):
            try:
                cb(cls._current)
            except Exception:
                # подписчик не должен ломать приложение
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
