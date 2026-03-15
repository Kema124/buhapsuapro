from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QTabWidget,
    QStatusBar,
    QMenu,
)
from PySide6.QtCore import Signal, QPoint

from database.models import Organization
from services.organization import get_organization

from ui.toolbar import create_toolbar
from ui.settings import SettingsWindow
from ui.archive_window import ArchiveWindow
from ui.documents_window import DocumentsWindow
from ui.tab_manager import TabManager, TabSpec
from ui.messenger import StatusMessenger, MsgType
from ui.theme_manager import ThemeManager
from ui.app_settings import AppSettings
from ui.sidebar import Sidebar


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

        # применяем сохранённые настройки
        st = AppSettings.load()
        ThemeManager.apply(st.theme)
        self.set_sidebar_visible(st.sidebar_visible, animate=False)

        self.refresh_org()

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

        # central: sidebar + tabs
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(10, 10, 10, 10)
        right_lay.setSpacing(8)
        root.addWidget(right, 1)

        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        right_lay.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.messenger = StatusMessenger(self.status_bar)

        self.tabs_manager = TabManager(self.tabs, main_window=self)

        # реестры/разделы
        self.tabs_manager.register(TabSpec(
            key="documents_hub",
            title="Документы",
            factory=lambda: DocumentsWindow(main_window=self),
            singleton=True,
        ))
        self.tabs_manager.register(TabSpec(
            key="archive",
            title="Архив",
            factory=lambda: ArchiveWindow(main_window=self),
            singleton=True,
        ))

        # справочники (каждый открывается отдельной вкладкой)
        self.tabs_manager.register(TabSpec(
            key="org",
            title="Организация",
            factory=lambda: __import__("ui.org_registration", fromlist=["OrganizationRegistration"])
            .OrganizationRegistration(main_window=self),
            singleton=True,
        ))
        self.tabs_manager.register(TabSpec(
            key="contagents",
            title="Контрагенты",
            factory=lambda: __import__("ui.contagents_window", fromlist=["ContagentsWindow"])
            .ContagentsWindow(main_window=self),
            singleton=True,
        ))
        self.tabs_manager.register(TabSpec(
            key="banks",
            title="Банки",
            factory=lambda: __import__("ui.banks_window", fromlist=["BanksWindow"])
            .BanksWindow(main_window=self),
            singleton=True,
        ))
        self.tabs_manager.register(TabSpec(
            key="taxes",
            title="Налоги",
            factory=lambda: __import__("ui.taxes_window", fromlist=["TaxesWindow"])
            .TaxesWindow(main_window=self),
            singleton=True,
        ))
        self.tabs_manager.register(TabSpec(
            key="expense_articles",
            title="Статьи расходов",
            factory=lambda: __import__("ui.expense_articles_window", fromlist=["ExpenseArticlesWindow"])
            .ExpenseArticlesWindow(main_window=self),
            singleton=True,
        ))

    # =========================================================
    # CONNECT
    # =========================================================

    def _connect_actions(self) -> None:
        self.back_action.triggered.connect(self.on_back)

        self.documents_action.triggered.connect(lambda: self.tabs_manager.open("documents_hub"))
        self.archive_action.triggered.connect(lambda: self.tabs_manager.open("archive"))
        self.settings_action.triggered.connect(self.open_settings)
        self.refresh_action.triggered.connect(self.refresh_current_tab)

        # "Справочники" -> меню выбора
        self.directories_action.triggered.connect(self.open_directories_menu)

        # sidebar buttons
        self.sidebar.btn_documents.clicked.connect(lambda: self.tabs_manager.open("documents_hub"))
        self.sidebar.btn_archive.clicked.connect(lambda: self.tabs_manager.open("archive"))
        self.sidebar.btn_settings.clicked.connect(self.open_settings)

        # в сайдбаре "Организация" и "Контрагенты" оставлены как быстрые входы
        self.sidebar.btn_org.clicked.connect(lambda: self.tabs_manager.open("org"))
        self.sidebar.btn_contagents.clicked.connect(lambda: self.tabs_manager.open("contagents"))

    # =========================================================
    # DIRECTORIES MENU
    # =========================================================

    def open_directories_menu(self) -> None:
        menu = QMenu(self)

        a_org = menu.addAction("Организация")
        a_cont = menu.addAction("Контрагенты")
        menu.addSeparator()
        a_banks = menu.addAction("Банки")
        a_taxes = menu.addAction("Налоги")
        a_exp = menu.addAction("Статьи расходов")

        act = menu.exec(self.mapToGlobal(QPoint(80, 60)))
        if act is None:
            return

        if act == a_org:
            self.tabs_manager.open("org")
        elif act == a_cont:
            self.tabs_manager.open("contagents")
        elif act == a_banks:
            self.tabs_manager.open("banks")
        elif act == a_taxes:
            self.tabs_manager.open("taxes")
        elif act == a_exp:
            self.tabs_manager.open("expense_articles")

    # =========================================================
    # SIDEBAR
    # =========================================================

    def set_sidebar_visible(self, visible: bool, animate: bool = True) -> None:
        # простое скрытие без сложной анимации (стабильно)
        self.sidebar.setVisible(visible)

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
