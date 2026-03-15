from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
from services.contracts import get_contracts_by_contagent

class ContractsWindow(QWidget):
    def __init__(self, contagent_id):
        super().__init__()
        self.contagent_id = contagent_id

        self.setWindowTitle("Договоры")
        self.setFixedSize(700, 400)

        self._init_ui()
        self.load_contracts()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Номер", "Дата", "Сумма"])

        # Важно: добавляем таблицу в локальный layout, а не в несуществующий self.layout
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_contracts(self):
        contracts = get_contracts_by_contagent(self.contagent_id)
        self.table.setRowCount(len(contracts))
        for row, c in enumerate(contracts):
            self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row, 1, QTableWidgetItem(c.number))
            self.table.setItem(row, 2, QTableWidgetItem(str(c.date)))
            self.table.setItem(row, 3, QTableWidgetItem(str(c.sum or "")))
