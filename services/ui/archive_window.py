from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui.archive_contagents_tab import ArchiveContagentsTab
from ui.archive_banks_tab import ArchiveBanksTab
from ui.archive_taxes_tab import ArchiveTaxesTab
from ui.archive_expense_articles_tab import ArchiveExpenseArticlesTab


class ArchiveWindow(QWidget):
    """Окно архива. Внутри — вкладки по типам объектов (как в 1С)."""

    def __init__(self, main_window=None) -> None:
        super().__init__()
        self.main_window = main_window

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.main_layout.addWidget(self.tabs)

        self.contagents_tab = ArchiveContagentsTab(main_window=main_window)
        self.banks_tab = ArchiveBanksTab(main_window=main_window)
        self.taxes_tab = ArchiveTaxesTab(main_window=main_window)
        self.expense_articles_tab = ArchiveExpenseArticlesTab(main_window=main_window)

        self.tabs.addTab(self.contagents_tab, "Контрагенты")
        self.tabs.addTab(self.banks_tab, "Банки")
        self.tabs.addTab(self.taxes_tab, "Налоги")
        self.tabs.addTab(self.expense_articles_tab, "Статьи расходов")

    def open_section(self, section: str) -> None:
        section = (section or "").lower()
        if section in {"contagents", "контрагенты"}:
            self.tabs.setCurrentWidget(self.contagents_tab)
        elif section in {"banks", "банки"}:
            self.tabs.setCurrentWidget(self.banks_tab)
        elif section in {"taxes", "налоги"}:
            self.tabs.setCurrentWidget(self.taxes_tab)
        elif section in {"expense_articles", "статьи расходов"}:
            self.tabs.setCurrentWidget(self.expense_articles_tab)

    def load_data(self) -> None:
        # Для кнопки «Обновить»
        for w in (self.contagents_tab, self.banks_tab, self.taxes_tab, self.expense_articles_tab):
            if hasattr(w, "load_data"):
                try:
                    w.load_data()  # type: ignore[attr-defined]
                except Exception:
                    pass
