from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui.org_registration import OrganizationRegistration
from ui.contagents_window import ContagentsWindow
from ui.banks_window import BanksWindow
from ui.taxes_window import TaxesWindow
from ui.expense_articles_window import ExpenseArticlesWindow


class DirectoriesWindow(QWidget):
    """Справочники (как раздел в 1С).

    Внутри — вкладки по объектам справочников.
    """

    def __init__(self, main_window=None) -> None:
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Справочники")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        self.org_tab = OrganizationRegistration(main_window=main_window)
        self.contagents_tab = ContagentsWindow(main_window=main_window)
        self.banks_tab = BanksWindow(main_window=main_window)
        self.taxes_tab = TaxesWindow(main_window=main_window)
        self.expenses_tab = ExpenseArticlesWindow(main_window=main_window)

        self.tabs.addTab(self.org_tab, "Организация")
        self.tabs.addTab(self.contagents_tab, "Контрагенты")
        self.tabs.addTab(self.banks_tab, "Банки")
        self.tabs.addTab(self.taxes_tab, "Налоги")
        self.tabs.addTab(self.expenses_tab, "Статьи расходов")

    def load_data(self) -> None:
        # для кнопки «Обновить»
        for w in (self.org_tab, self.contagents_tab, self.banks_tab, self.taxes_tab, self.expenses_tab):
            if hasattr(w, "load_data"):
                try:
                    w.load_data()  # type: ignore[attr-defined]
                except Exception:
                    pass
