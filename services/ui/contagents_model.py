from __future__ import annotations

from typing import Any, Sequence

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex


class ContagentsTableModel(QAbstractTableModel):
    HEADERS: list[str] = [
        "Наименование",
        "Тип",
        "ИНН",
        "КПП",
        "Адрес",
        "Примечание",
    ]

    def __init__(self, contagents: Sequence[Any] | None = None) -> None:
        super().__init__()
        self._data: list[Any] = list(contagents) if contagents is not None else []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._data):
            return None

        contagent = self._data[row]

        # PySide6: роли лежат в Qt.ItemDataRole.*
        if role == int(Qt.ItemDataRole.DisplayRole):
            match col:
                case 0:
                    return getattr(contagent, "name", "")

                case 1:
                    org_type = getattr(contagent, "organization_type", None)  # ✅ было contagent.type (ошибка)
                    if org_type == "company":
                        return "Юр. лицо"
                    if org_type == "ip":
                        return "ИП"
                    if org_type == "person":
                        return "Физ. лицо"
                    return ""

                case 2:
                    return getattr(contagent, "inn", "") or ""

                case 3:
                    return getattr(contagent, "kpp", "") or ""

                case 4:
                    return getattr(contagent, "address", "") or ""

                case 5:
                    return getattr(contagent, "note", "") or ""

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = int(Qt.ItemDataRole.DisplayRole)) -> Any:
        if role != int(Qt.ItemDataRole.DisplayRole):
            return None

        # PySide6: ориентации лежат в Qt.Orientation.*
        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
            return None

        # вертикальные заголовки: номера строк с 1
        return section + 1

    def set_data(self, contagents: Sequence[Any]) -> None:
        self.beginResetModel()
        self._data = list(contagents)
        self.endResetModel()

    def get_contagent(self, row: int) -> Any | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
