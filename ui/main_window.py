from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable, Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStatusBar,
)
from PySide6.QtCore import Signal

from database.models import Organization
from services.organization import get_organization

from ui.toolbar import create_toolbar
from ui.settings import SettingsWindow
from ui.archive_window import ArchiveWindow
from ui.directories_window import DirectoriesWindow
from ui.documents_window import DocumentsWindow
from ui.tab_manager import TabManager, TabSpec
from ui.messenger import StatusMessenger, MsgType
from ui.theme_manager import ThemeManager
from ui.app_settings import AppSettings


@runtime_checkable
class Loadable(Protocol):
    def load_data(self) -> None: ...


class MainWindow(QMainWindow):
    form_closed = Signal()

    def __init__(self, organization: Organization | None, on_back: Callable[[], None]):
        super().__init__()
        self.organization = organization
        self.on_back = on_back

        self.settings_window: SettingsWindow | None = None

        self._init_ui()
        self._connect_actions()

        # применяем сохранённые настройки (тема и т.п.)
        st = AppSettings.load()
        ThemeManager.apply(st.theme)

    # =========================================================
    # UI
    # =========================================================

    def _init_ui(self) -> None:
        (
            toolbar,
            self.directories_action,
            self.documents_action,
            self.archive_action,
            self.settings_action,
            self.refresh_action,
            self.back_action,
        ) = create_toolbar(self)

        self.addToolBar(toolbar)
        self.back_action.triggered.connect(self.on_back)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setCentralWidget(central)

        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.messenger = StatusMessenger(self.status_bar)

        self.tabs_manager = TabManager(self.tabs, main_window=self)

        self.tabs_manager.register(TabSpec(
            key="documents",
            title="Документы",
            factory=lambda: DocumentsWindow(main_window=self),
            singleton=True,
        ))
        self.tabs_manager.register(TabSpec(
            key="directories",
            title="Справочники",
            factory=lambda: DirectoriesWindow(main_window=self),
            singleton=True,
        ))
        self.tabs_manager.register(TabSpec(
            key="archive",
            title="Архив",
            factory=lambda: ArchiveWindow(main_window=self),
            singleton=True,
        ))

        self.refresh_org()

    # =========================================================
    # CONNECT
    # =========================================================

    def _connect_actions(self) -> None:
        self.documents_action.triggered.connect(lambda: self.tabs_manager.open("documents"))
        self.directories_action.triggered.connect(lambda: self.tabs_manager.open("directories"))
        self.archive_action.triggered.connect(lambda: self.tabs_manager.open("archive"))
        self.settings_action.triggered.connect(self.open_settings)
        self.refresh_action.triggered.connect(self.refresh_current_tab)

    # =========================================================
    # STATUS
    # =========================================================

    def show_message(self, message: str, msg_type: MsgType = "info", timeout: int = 5000) -> None:
        self.messenger.show(message, msg_type=msg_type, timeout=timeout)

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh_current_tab(self) -> None:
        w = self.tabs.currentWidget()
        if w is None:
            self.show_message("Нет открытой вкладки", "info", 1500)
            return

        if isinstance(w, Loadable):
            try:
                w.load_data()
                self.show_message("Обновлено", "success", 1500)
            except Exception as e:
                self.show_message(str(e), "error", 6000)
        else:
            # ничего обновлять
            self.show_message("Эту вкладку обновлять не нужно", "info", 1500)

    # =========================================================
    # ORG
    # =========================================================

    def refresh_org(self) -> None:
        self.organization = get_organization()
        if self.organization:
            self.setWindowTitle(f"БухАпсуаПро — {self.organization.name}")
        else:
            self.setWindowTitle("БухАпсуаПро")

    # =========================================================
    # SETTINGS
    # =========================================================

    def open_settings(self) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(main_window=self)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    # =========================================================
    # HELPERS
    # =========================================================

    def close_widget_tab(self, widget: QWidget) -> None:
        idx = self.tabs.indexOf(widget)
        if idx >= 0:
            self.tabs_manager.close(idx)
