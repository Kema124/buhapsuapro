from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QComboBox, QMessageBox
)

from services.contagents import (
    get_deleted_contagent_by_id,
    restore_contagent,
    delete_contagent_forever,
)


class ContagentArchiveCardTab(QWidget):
    """
    Карточка архивного контрагента как вкладка (read-only),
    с кнопками: Восстановить / Удалить навсегда / Закрыть.
    """

    def __init__(
        self,
        main_window: Any,
        *,
        contagent_id: int,
        tab_key: str,
        on_restored: Callable[[], None] | None = None,
        on_deleted: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.contagent_id = contagent_id
        self.tab_key = tab_key
        self.on_restored = on_restored
        self.on_deleted = on_deleted

        self._init_ui()
        self._load()

    def _status(self, msg: str, t: str = "info", timeout: int = 5000) -> None:
        if self.main_window is not None:
            self.main_window.show_message(msg, t, timeout)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Роль"))
        self.role_input = QComboBox()
        self.role_input.addItem("Покупатель", "buyer")
        self.role_input.addItem("Поставщик", "supplier")
        self.role_input.addItem("Покупатель и поставщик", "both")
        self.role_input.setEnabled(False)
        layout.addWidget(self.role_input)

        layout.addWidget(QLabel("Тип организации"))
        self.org_type_input = QComboBox()
        self.org_type_input.addItem("Юридическое лицо", "company")
        self.org_type_input.addItem("ИП", "ip")
        self.org_type_input.addItem("Физическое лицо", "person")
        self.org_type_input.setEnabled(False)
        layout.addWidget(self.org_type_input)

        layout.addWidget(QLabel("Название"))
        self.name_input = QLineEdit()
        self.name_input.setReadOnly(True)
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("ИНН"))
        self.inn_input = QLineEdit()
        self.inn_input.setReadOnly(True)
        layout.addWidget(self.inn_input)

        layout.addWidget(QLabel("КПП"))
        self.kpp_input = QLineEdit()
        self.kpp_input.setReadOnly(True)
        layout.addWidget(self.kpp_input)

        layout.addWidget(QLabel("Адрес"))
        self.address_input = QLineEdit()
        self.address_input.setReadOnly(True)
        layout.addWidget(self.address_input)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.restore_btn = QPushButton("↩ Восстановить")
        self.delete_btn = QPushButton("🗑 Удалить навсегда")
        self.close_btn = QPushButton("Закрыть")

        btn_layout.addWidget(self.restore_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.restore_btn.clicked.connect(self._restore)
        self.delete_btn.clicked.connect(self._delete_forever)
        self.close_btn.clicked.connect(self._close_tab)

    def _load(self) -> None:
        c = get_deleted_contagent_by_id(self.contagent_id)
        if c is None:
            self._status("Архивный контрагент не найден", "error", 6000)
            return

        self.role_input.setCurrentIndex(self.role_input.findData(c.role))
        self.org_type_input.setCurrentIndex(self.org_type_input.findData(c.organization_type))
        self.name_input.setText(c.name or "")
        self.inn_input.setText(c.inn or "")
        self.kpp_input.setText(c.kpp or "")
        self.address_input.setText(c.address or "")

    def _restore(self) -> None:
        try:
            restore_contagent(self.contagent_id)
            self._status("Контрагент восстановлен", "success", 4000)

            if self.on_restored is not None:
                self.on_restored()

            self._close_tab()
        except Exception as e:
            self._status(f"Не удалось восстановить: {e}", "error", 7000)

    def _delete_forever(self) -> None:
        ans = QMessageBox.question(
            self,
            "Удаление навсегда",
            "Удалить контрагента навсегда? Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_contagent_forever(self.contagent_id)
            self._status("Контрагент удалён навсегда", "success", 5000)

            if self.on_deleted is not None:
                self.on_deleted()

            self._close_tab()
        except Exception as e:
            self._status(f"Не удалось удалить навсегда: {e}", "error", 7000)

    def _close_tab(self) -> None:
        if self.main_window is not None and hasattr(self.main_window, "tabs_manager"):
            self.main_window.tabs_manager.close_by_key(self.tab_key)
