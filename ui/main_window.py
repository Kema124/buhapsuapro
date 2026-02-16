from __future__ import annotations

from typing import Callable, Optional, Protocol, runtime_checkable

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QStatusBar
from PySide6.QtCore import Qt

from database.models import Organization
from services.organization import get_organization

from ui.toolbar import create_toolbar
from ui.settings import SettingsWindow
from ui.archive_window import ArchiveWindow
from ui.org_registration import OrganizationRegistration
from ui.contagents_window import ContagentsWindow
from ui.documents_window import DocumentsWindow
from ui.tab_manager import TabManager, TabSpec


@runtime_checkable
class SupportsLoadData(Protocol):
    def load_data(self) -> None: ...


class MainWindow(QMainWindow):
    def __init__(self, organization: Optional[Organization], on_back: Callable[[], None]):
        super().__init__()
        self.organization = organization
        self.on_back = on_back

        self.settings_window: SettingsWindow | None = None

        self._init_ui()
        self._connect_actions()
        self.refresh_org()

    def _init_ui(self) -> None:
        tb, self.org_action, self.contagents_action, self.archive_action, self.documents_action, \
        self.settings_action, self.refresh_action, self.back_action = create_toolbar(self)

        self.addToolBar(tb)
        self.back_action.triggered.connect(self.on_back)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(12, 10, 12, 10)
        self.setCentralWidget(central)

        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        lay.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.tabs_manager = TabManager(self.tabs, main_window=self)

        self.tabs_manager.register(TabSpec(
            key="documents",
            title="Документы",
            factory=lambda: DocumentsWindow(main_window=self),
            singleton=True,
        ))

        self.tabs_manager.register(TabSpec(
            key="contagents",
            title="Контрагенты",
            factory=lambda: ContagentsWindow(main_window=self),
            singleton=True,
        ))

        self.tabs_manager.register(TabSpec(
            key="archive",
            title="Архив",
            factory=lambda: ArchiveWindow(main_window=self),
            singleton=True,
        ))

        self.tabs_manager.register(TabSpec(
            key="org",
            title="Организация",
            factory=lambda: OrganizationRegistration(on_saved=self.refresh_org, main_window=self),
            singleton=True,
        ))

    def _connect_actions(self) -> None:
        self.settings_action.triggered.connect(self.open_settings)
        self.documents_action.triggered.connect(lambda: self.tabs_manager.open("documents"))
        self.contagents_action.triggered.connect(lambda: self.tabs_manager.open("contagents"))
        self.archive_action.triggered.connect(lambda: self.tabs_manager.open("archive"))
        self.org_action.triggered.connect(lambda: self.tabs_manager.open("org"))
        self.refresh_action.triggered.connect(self.refresh_current_tab)

    def show_message(self, message: str, msg_type: str = "info", timeout: int = 5000) -> None:
        # msg_type оставляем, чтобы не ломать совместимость
        self.statusBar().showMessage(message, timeout)

    def refresh_current_tab(self) -> None:
        w = self.tabs.currentWidget()
        if w is None:
            self.show_message("Нет открытых вкладок", "warning", 2000)
            return

        if isinstance(w, SupportsLoadData):
            try:
                w.load_data()
                self.show_message("Обновлено", "success", 1500)
            except Exception as e:
                self.show_message(str(e), "error", 6000)
        else:
            self.show_message("Эта вкладка не поддерживает обновление", "info", 2500)

    def refresh_org(self) -> None:
        self.organization = get_organization()
        if self.organization:
            self.setWindowTitle(f"БухАпсуаПро — {self.organization.name}")
        else:
            self.setWindowTitle("БухАпсуаПро")

    def open_settings(self) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(main_window=self)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
