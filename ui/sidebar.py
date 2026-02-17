from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt

from ui.assets import load_icon
from ui.theme_manager import ThemeManager


class Sidebar(QWidget):
    """Левая панель (как в 1С), можно скрывать в настройках."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(220)
        self.setObjectName("Sidebar")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        self.btn_documents = QPushButton("Документы")
        self.btn_org = QPushButton("Организация")
        self.btn_contagents = QPushButton("Контрагенты")
        self.btn_archive = QPushButton("Архив")
        self.btn_settings = QPushButton("Настройки")

        for b in (self.btn_documents, self.btn_org, self.btn_contagents, self.btn_archive, self.btn_settings):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setObjectName("SidebarButton")
            b.setMinimumHeight(36)
            lay.addWidget(b)

        lay.addStretch(1)

        ThemeManager.subscribe(self._apply_icons)
        self._apply_icons(ThemeManager.current())

    def _apply_icons(self, theme: str) -> None:
        # Сайдбар зависит от темы: на тёмной — светлые иконки
        color = "#ffffff" if theme == "dark" else "#0f172a"
        self.btn_documents.setIcon(load_icon("documents.svg", color=color))
        self.btn_org.setIcon(load_icon("org.svg", color=color))
        self.btn_contagents.setIcon(load_icon("users.svg", color=color))
        self.btn_archive.setIcon(load_icon("archive.svg", color=color))
        self.btn_settings.setIcon(load_icon("settings.svg", color=color))
