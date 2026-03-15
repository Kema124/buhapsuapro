from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QComboBox
)
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression

from services.organization import get_organization, create_organization, update_organization


class OrganizationRegistration(QWidget):
    def __init__(self, on_saved=None, main_window=None):
        super().__init__()
        self.on_saved = on_saved
        self.main_window = main_window
        self.organization = None
        self.is_modified = False

        self.setWindowTitle("Организация")

        self._init_ui()
        self.reload()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.main_layout.addWidget(QLabel("Тип"))
        self.type_input = QComboBox()
        self.type_input.addItem("Юридическое лицо", "company")
        self.type_input.addItem("Физическое лицо", "person")
        self.type_input.currentIndexChanged.connect(self._type_changed)
        self.main_layout.addWidget(self.type_input)

        self.main_layout.addWidget(QLabel("Название организации"))
        self.name_input = QLineEdit()
        self.main_layout.addWidget(self.name_input)

        self.inn_input = QLineEdit()
        self.inn_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,8}$")))
        self.main_layout.addWidget(QLabel("ИНН (8 цифр)"))
        self.main_layout.addWidget(self.inn_input)

        self.kpp_input = QLineEdit()
        self.kpp_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,9}$")))
        self.main_layout.addWidget(QLabel("КПП (9 цифр)"))
        self.main_layout.addWidget(self.kpp_input)

        self.ogrn_input = QLineEdit()
        self.ogrn_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[A-Za-z0-9]{0,11}$")))
        self.main_layout.addWidget(QLabel("ОГРН (11 символов)"))
        self.main_layout.addWidget(self.ogrn_input)

        self.address_input = QLineEdit()
        self.main_layout.addWidget(QLabel("Адрес"))
        self.main_layout.addWidget(self.address_input)

        # --- Кнопки как в контрагенте ---
        btns = QHBoxLayout()
        self.save_btn = QPushButton("Записать")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        btns.addStretch()
        self.main_layout.addLayout(btns)

        self.save_btn.clicked.connect(self._save_only)
        self.ok_btn.clicked.connect(self._save_and_close)
        self.cancel_btn.clicked.connect(self._close_tab)

        # mark modified
        for w in (self.name_input, self.inn_input, self.kpp_input, self.ogrn_input, self.address_input):
            w.textChanged.connect(self._mark_modified)
        self.type_input.currentIndexChanged.connect(self._mark_modified)

    def _mark_modified(self):
        self.is_modified = True

    def _msg(self, text: str, kind: str = "info", timeout: int = 4000):
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def reload(self):
        self.organization = get_organization()
        self._load_data()

    def _load_data(self):
        org = self.organization
        if not org:
            self.name_input.setText("")
            self.inn_input.setText("")
            self.kpp_input.setText("")
            self.ogrn_input.setText("")
            self.address_input.setText("")
            self.type_input.setCurrentIndex(0)
            self._type_changed()
            self.is_modified = False
            return

        self.name_input.setText(org.name)
        self.inn_input.setText(org.inn)
        self.kpp_input.setText(org.kpp or "")
        self.ogrn_input.setText(org.ogrn or "")
        self.address_input.setText(org.address or "")

        self.type_input.setCurrentIndex(1 if getattr(org, "organization_type", None) == "person" else 0)
        self._type_changed()
        self.is_modified = False

    def _type_changed(self):
        is_person = self.type_input.currentData() == "person"
        self.kpp_input.setEnabled(not is_person)
        self.ogrn_input.setEnabled(not is_person)
        if is_person:
            self.kpp_input.setText("")
            self.ogrn_input.setText("")

    def _validate(self) -> bool:
        if not self.name_input.text().strip():
            self._msg("Название организации обязательно", "warning", 3000)
            return False

        inn = self.inn_input.text().strip()
        if len(inn) != 8:
            self._msg("ИНН должен содержать 8 цифр", "warning", 3000)
            return False

        if self.kpp_input.isEnabled():
            kpp = self.kpp_input.text().strip()
            if kpp and len(kpp) != 9:
                self._msg("КПП должен содержать 9 цифр", "warning", 3000)
                return False

        if self.ogrn_input.isEnabled():
            ogrn = self.ogrn_input.text().strip()
            if ogrn and len(ogrn) != 11:
                self._msg("ОГРН должен содержать 11 символов", "warning", 3000)
                return False

        return True

    def _collect(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "inn": self.inn_input.text().strip(),
            "kpp": self.kpp_input.text().strip() if self.kpp_input.isEnabled() else None,
            "ogrn": self.ogrn_input.text().strip() if self.ogrn_input.isEnabled() else None,
            "address": self.address_input.text().strip() or None,
            "organization_type": self.type_input.currentData(),
        }

    def _save(self) -> bool:
        if not self.is_modified:
            self._msg("Нет изменений", "info", 1500)
            return False

        if not self._validate():
            return False

        data = self._collect()
        try:
            if self.organization:
                update_organization(data)
            else:
                create_organization(data)

            self.organization = get_organization()
            self.is_modified = False

            if self.on_saved:
                self.on_saved()

            self._msg("Организация сохранена", "success", 2500)
            return True

        except Exception as e:
            self._msg(str(e), "error", 6000)
            return False

    def _save_only(self):
        self._save()

    def _save_and_close(self):
        if self._save():
            self._close_tab()

    def _close_tab(self):
        if self.main_window and hasattr(self.main_window, "close_widget_tab"):
            self.main_window.close_widget_tab(self)
        else:
            self.close()
