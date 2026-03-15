from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QListWidget, QPushButton, QMessageBox
)
import os
from services.organization import load_registry, create_new_database


class DatabaseSelector(QWidget):
    def __init__(self, on_selected):
        super().__init__()
        self.on_selected = on_selected

        self.setWindowTitle("Выбор организации")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Выберите организацию:"))

        self.list_widget = QListWidget()
        self.registry = load_registry()

        for name in self.registry.keys():
            self.list_widget.addItem(name)

        layout.addWidget(self.list_widget)

        btn = QPushButton("Открыть")
        btn.clicked.connect(self.select)

        # 🔥 двойной клик
        self.list_widget.itemDoubleClicked.connect(self.select)

        layout.addWidget(btn)

        self.setLayout(layout)

    def select(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите организацию")
            return

        org_name = item.text()
        db_path = self.registry[org_name]

        # если путь относительный — делаем абсолютным
        db_path = os.path.abspath(db_path)

        # если базы нет — создаём её автоматически
        if not os.path.exists(db_path):
            # create_new_database сохраняет путь в registry и возвращает db_path
            db_path = os.path.abspath(create_new_database(org_name))

        print("SELECTED DB:", db_path)
        self.on_selected(db_path)
        self.close()


    def reload(self):
        self.list_widget.clear()
        self.registry = load_registry()
        for name in self.registry.keys():
            self.list_widget.addItem(name)
