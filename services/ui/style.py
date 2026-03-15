from PySide6.QtWidgets import QApplication


LIGHT_STYLE = """
QMainWindow {
    background-color: #f4f6f9;
}

QToolBar {
    background-color: #1f3c73;
    color: white;
    spacing: 6px;
    padding: 6px;
}

QToolButton {
    color: white;
    background: transparent;
    padding: 6px 10px;
    border-radius: 4px;
}

QToolButton:hover {
    background-color: #2c5fb8;
}

QTabWidget::pane {
    border: none;
}

QTabBar::tab {
    background: #e8eef7;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background: white;
    font-weight: bold;
}

QTableWidget {
    background-color: white;
    border: 1px solid #dbe2ef;
    gridline-color: #e6ecf5;
}

QTableWidget::item:selected {
    background-color: #cde1ff;
    color: black;
}

QPushButton {
    background-color: #1f3c73;
    color: white;
    border-radius: 4px;
    padding: 6px 10px;
}

QPushButton:hover {
    background-color: #2c5fb8;
}

QStatusBar {
    background-color: #1f3c73;
    color: white;
    font-weight: bold;
}
"""


DARK_STYLE = """
QMainWindow {
    background-color: #1e2430;
    color: #e8eef7;
}

QToolBar {
    background-color: #0f2f5c;
    color: white;
}

QTabBar::tab {
    background: #2a3142;
    padding: 8px 16px;
}

QTabBar::tab:selected {
    background: #364058;
}

QTableWidget {
    background-color: #2a3142;
    color: white;
    gridline-color: #364058;
}

QTableWidget::item:selected {
    background-color: #4caf50;
    color: white;
}

QPushButton {
    background-color: #1b4f9c;
    color: white;
    border-radius: 4px;
    padding: 6px 10px;
}

QPushButton:hover {
    background-color: #4caf50;
}

QStatusBar {
    background-color: #0f2f5c;
    color: white;
}
"""


def apply_light(app: QApplication):
    app.setStyleSheet(LIGHT_STYLE)


def apply_dark(app: QApplication):
    app.setStyleSheet(DARK_STYLE)
