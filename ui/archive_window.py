from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui.archive_contagents_tab import ArchiveContagentsTab
from ui.archive_contracts_tab import ArchiveContractsTab


class ArchiveWindow(QWidget):
    """Окно архива. Внутри — вкладки по типам объектов (как в 1С)."""

    def __init__(self, main_window=None) -> None:
        super().__init__()
        self.main_window = main_window

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.layout.addWidget(self.tabs)

        self.contagents_tab = ArchiveContagentsTab(main_window=main_window)
        self.contracts_tab = ArchiveContractsTab(main_window=main_window)

        self.tabs.addTab(self.contagents_tab, "Контрагенты")
        self.tabs.addTab(self.contracts_tab, "Договоры")

    def open_section(self, section: str) -> None:
        section = (section or "").lower()
        if section in {"contagents", "контрагенты"}:
            self.tabs.setCurrentWidget(self.contagents_tab)
        elif section in {"contracts", "договоры"}:
            self.tabs.setCurrentWidget(self.contracts_tab)

    def load_data(self) -> None:
        # Для кнопки «Обновить» в тулбаре
        self.contagents_tab.load_data()
        self.contracts_tab.load_data()
