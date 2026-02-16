from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel

from ui.theme_manager import ThemeManager


class SettingsWindow(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Настройки")
        self.setFixedSize(420, 260)

        layout = QVBoxLayout(self)

        title = QLabel("Параметры интерфейса")
        title.setObjectName("SettingsTitle")
        layout.addWidget(title)

        self.dark_theme = QCheckBox("Тёмная тема")
        self.dark_theme.setChecked(ThemeManager.current() == "dark")
        self.dark_theme.stateChanged.connect(self._toggle_theme)
        layout.addWidget(self.dark_theme)

        layout.addStretch(1)

    def _toggle_theme(self) -> None:
        ThemeManager.apply("dark" if self.dark_theme.isChecked() else "light")
        if self.main_window:
            self.main_window.show_message("Тема применена", "success", 2000)
