from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Qt

from ui.assets import load_icon
from ui.theme_manager import ThemeManager


class Sidebar(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setMaximumWidth(220)

        self._theme = ThemeManager.current()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.buttons: dict[str, QPushButton] = {}

        self.btn_home = self._add(layout, "Главная", "home.svg", "home")
        self.btn_org = self._add(layout, "Организация", "organization.svg", "org")
        self.btn_contagents = self._add(layout, "Контрагенты", "users.svg", "contagents")
        self.btn_documents = self._add(layout, "Документы", "documents.svg", "documents")
        self.btn_archive = self._add(layout, "Архив", "archive.svg", "archive")
        self.btn_settings = self._add(layout, "Настройки", "settings.svg", "settings")

        layout.addStretch()
        self.set_active("home")

        ThemeManager.subscribe(self._on_theme_changed)
        self.apply_icons()

    def closeEvent(self, event):
        ThemeManager.unsubscribe(self._on_theme_changed)
        super().closeEvent(event)

    def _icon_color(self) -> str:
        return "#e8eef7" if self._theme == "dark" else "#22324a"

    def apply_icons(self) -> None:
        c = self._icon_color()
        self.btn_home.setIcon(load_icon("home.svg", color=c))
        self.btn_org.setIcon(load_icon("organization.svg", color=c))
        self.btn_contagents.setIcon(load_icon("users.svg", color=c))
        self.btn_documents.setIcon(load_icon("documents.svg", color=c))
        self.btn_archive.setIcon(load_icon("archive.svg", color=c))
        self.btn_settings.setIcon(load_icon("settings.svg", color=c))

    def _on_theme_changed(self, theme: str) -> None:
        self._theme = theme
        self.apply_icons()

    def _add(self, layout: QVBoxLayout, text: str, _icon: str, key: str) -> QPushButton:
        b = QPushButton(text)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setObjectName("SidebarButton")
        b.setProperty("active", False)
        b.setMinimumHeight(36)
        b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(b)
        self.buttons[key] = b
        return b

    def set_active(self, key: str) -> None:
        for k, btn in self.buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
