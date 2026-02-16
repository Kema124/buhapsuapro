from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QHBoxLayout
)

from ui.app_settings import AppSettings, UISettings
from ui.theme_manager import ThemeManager


class SettingsWindow(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Настройки")
        self.setFixedSize(420, 260)

        self._init_ui()
        self._load()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Интерфейс"))

        self.dark_theme = QCheckBox("Тёмная тема")
        layout.addWidget(self.dark_theme)

        # sidebar_visible оставили на будущее (сейчас сайдбар может отсутствовать)
        self.sidebar_visible = QCheckBox("Показывать боковую панель")
        layout.addWidget(self.sidebar_visible)

        btns = QHBoxLayout()
        self.btn_apply = QPushButton("Применить")
        self.btn_close = QPushButton("Закрыть")
        btns.addWidget(self.btn_apply)
        btns.addWidget(self.btn_close)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.btn_apply.clicked.connect(self.apply)
        self.btn_close.clicked.connect(self.close)

    def _load(self):
        st = AppSettings.load()
        self.dark_theme.setChecked(st.theme == "dark")
        self.sidebar_visible.setChecked(st.sidebar_visible)

    def apply(self):
        st = UISettings(
            theme="dark" if self.dark_theme.isChecked() else "light",
            sidebar_visible=self.sidebar_visible.isChecked(),
        )
        AppSettings.save(st)
        ThemeManager.apply(st.theme)

        if self.main_window:
            self.main_window.show_message("Настройки применены", "success", 2000)
