import sys

from PySide6.QtWidgets import QApplication

from ui.db_selector import DatabaseSelector
from ui.main_window import MainWindow
from database.db import init_db
from database.schema import ensure_schema
from services.organization import get_organization

from ui.assets import load_icon
from ui.theme_manager import ThemeManager
from ui.app_settings import AppSettings


class AccountingApp:
    def __init__(self, app: QApplication):
        self.app = app
        self.db_selector: DatabaseSelector | None = None
        self.main_window: MainWindow | None = None

        self.db_selector = DatabaseSelector(on_selected=self.start_app)

    def start_app(self, db_path: str) -> None:
        engine = init_db(db_path)
        # Мягкая синхронизация схемы (создание недостающих таблиц/полей)
        ensure_schema(engine)

        org = get_organization()

        if self.main_window is not None:
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None

        self.main_window = MainWindow(
            organization=org,
            on_back=self.back_to_selector
        )
        self.main_window.show()

        if self.db_selector is not None:
            self.db_selector.hide()

    def back_to_selector(self) -> None:
        if self.main_window is not None:
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None

        if self.db_selector is None:
            self.db_selector = DatabaseSelector(on_selected=self.start_app)

        self.db_selector.show()
        self.db_selector.raise_()
        self.db_selector.activateWindow()

    def run(self) -> int:
        if self.db_selector is None:
            self.db_selector = DatabaseSelector(on_selected=self.start_app)
        self.db_selector.show()
        return self.app.exec()


def main() -> int:
    app = QApplication(sys.argv)

    # Иконка приложения (можно заменить на .ico)
    app.setWindowIcon(load_icon("app_icon.png"))

    # Тема по настройкам
    st = AppSettings.load()
    ThemeManager.apply(st.theme)

    accounting = AccountingApp(app)
    return accounting.run()


if __name__ == "__main__":
    sys.exit(main())
