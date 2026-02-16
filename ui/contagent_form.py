from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QHBoxLayout, QMessageBox
)
from PySide6.QtGui import QIntValidator

from services.contagents import (
    get_contagent_by_id,
    create_contagent,
    update_contagent,
)


class ContagentForm(QDialog):
    def __init__(
        self,
        contagent_id: int | None = None,
        mode: str = "create",
        on_saved: Callable[[], None] | None = None,
        main_window: Any | None = None,
    ) -> None:
        super().__init__()

        self.mode = mode
        self.contagent_id = contagent_id
        self.on_saved = on_saved
        self.main_window = main_window

        self.contagent: Any | None = None
        self.is_modified = False

        self.setWindowTitle("Контрагент")
        self.setMinimumSize(520, 420)  # ✅ можно менять размер

        self._init_ui()

        if self.contagent_id is not None:
            self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Роль"))
        self.role_input = QComboBox()
        self.role_input.addItem("Покупатель", "buyer")
        self.role_input.addItem("Поставщик", "supplier")
        self.role_input.addItem("Покупатель и поставщик", "both")
        layout.addWidget(self.role_input)

        layout.addWidget(QLabel("Тип организации"))
        self.org_type_input = QComboBox()
        self.org_type_input.addItem("Юридическое лицо", "company")
        self.org_type_input.addItem("ИП", "ip")
        self.org_type_input.addItem("Физическое лицо", "person")
        self.org_type_input.currentIndexChanged.connect(self._org_type_changed)
        layout.addWidget(self.org_type_input)

        layout.addWidget(QLabel("Название *"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("ИНН"))
        self.inn_input = QLineEdit()
        self.inn_input.setValidator(QIntValidator())
        self.inn_input.setMaxLength(8)
        layout.addWidget(self.inn_input)

        layout.addWidget(QLabel("КПП"))
        self.kpp_input = QLineEdit()
        self.kpp_input.setValidator(QIntValidator())
        self.kpp_input.setMaxLength(9)
        layout.addWidget(self.kpp_input)

        layout.addWidget(QLabel("Адрес"))
        self.address_input = QLineEdit()
        layout.addWidget(self.address_input)

        self.active_checkbox = QCheckBox("Активен")
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)

        self.deleted_checkbox = QCheckBox("Удалён")
        self.deleted_checkbox.setChecked(False)
        layout.addWidget(self.deleted_checkbox)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Записать")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self._save_only)
        self.ok_btn.clicked.connect(self._ok_clicked)
        self.cancel_btn.clicked.connect(self.close_form)

        self._org_type_changed()

        # изменения
        self.name_input.textChanged.connect(self._mark_modified)
        self.inn_input.textChanged.connect(self._mark_modified)
        self.kpp_input.textChanged.connect(self._mark_modified)
        self.address_input.textChanged.connect(self._mark_modified)
        self.role_input.currentIndexChanged.connect(self._mark_modified)
        self.org_type_input.currentIndexChanged.connect(self._mark_modified)
        self.active_checkbox.stateChanged.connect(self._mark_modified)
        self.deleted_checkbox.stateChanged.connect(self._mark_modified)

    def _mark_modified(self) -> None:
        self.is_modified = True

    def _org_type_changed(self) -> None:
        is_company = self.org_type_input.currentData() == "company"
        self.kpp_input.setEnabled(bool(is_company))
        if not is_company:
            self.kpp_input.clear()

    def _load_data(self) -> None:
        if self.contagent_id is None:
            return
        self.contagent = get_contagent_by_id(self.contagent_id)
        if not self.contagent:
            return

        self.role_input.setCurrentIndex(self.role_input.findData(self.contagent.role))
        self.org_type_input.setCurrentIndex(self.org_type_input.findData(self.contagent.organization_type))
        self.name_input.setText(self.contagent.name or "")
        self.inn_input.setText(self.contagent.inn or "")
        self.kpp_input.setText(self.contagent.kpp or "")
        self.address_input.setText(self.contagent.address or "")
        self.active_checkbox.setChecked(bool(self.contagent.is_active))
        self.deleted_checkbox.setChecked(bool(self.contagent.is_deleted))

        self.is_modified = False

    def _validate(self) -> bool:
        name = self.name_input.text().strip()
        if not name:
            self._status("Название обязательно", "error")
            return False

        inn = self.inn_input.text().strip()
        kpp = self.kpp_input.text().strip()

        if inn and len(inn) != 8:
            self._status("ИНН должен содержать 8 цифр", "error")
            return False

        if kpp and len(kpp) != 9:
            self._status("КПП должен содержать 9 цифр", "error")
            return False

        return True

    def _collect_data(self) -> dict[str, Any]:
        return {
            "name": self.name_input.text().strip(),
            "role": self.role_input.currentData(),
            "organization_type": self.org_type_input.currentData(),
            "inn": self.inn_input.text().strip() or None,
            "kpp": self.kpp_input.text().strip() or None,
            "address": self.address_input.text().strip() or None,
            "is_active": bool(self.active_checkbox.isChecked()),
            "is_deleted": bool(self.deleted_checkbox.isChecked()),
        }

    def _status(self, msg: str, t: str = "info") -> None:
        if self.main_window is not None:
            self.main_window.show_message(msg, t, 5000)
        else:
            # если main_window не передали — хотя бы QMessageBox
            QMessageBox.warning(self, "Сообщение", msg)

    def _save(self) -> bool:
        # ✅ ВАЖНО: для create сохраняем даже если is_modified не “сработал”
        if self.mode == "edit" and not self.is_modified:
            # нет изменений — считаем ОК успешным
            return True

        if not self._validate():
            return False

        data = self._collect_data()

        try:
            if self.mode == "edit" and self.contagent_id is not None:
                update_contagent(self.contagent_id, data)
            else:
                create_contagent(data)
        except Exception as e:
            self._status(str(e), "error")
            return False

        self.is_modified = False
        return True

    def _save_only(self) -> None:
        if self._save():
            self._status("Контрагент сохранён", "success")
            if self.on_saved is not None:
                self.on_saved()

    def _ok_clicked(self) -> None:
        if self._save():
            if self.on_saved is not None:
                self.on_saved()
            self.accept()

    def close_form(self) -> None:
        if self.is_modified:
            ans = QMessageBox.question(
                self,
                "Несохранённые данные",
                "Есть несохранённые изменения. Закрыть форму?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ans == QMessageBox.StandardButton.No:
                return
        self.reject()
