from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from services.organization import create_organization, get_organization, update_organization
from ui.common.card_helpers import build_card_shell, build_footer, confirm_close_if_modified


class OrganizationRegistration(QWidget):
    def __init__(self, on_saved=None, main_window=None):
        super().__init__()
        self.on_saved = on_saved
        self.main_window = main_window
        self.organization = None
        self.is_modified = False

        root, self.name_input, self.tabs = build_card_shell(self, 'Организация', 'Наименование организации *', 760)
        self._init_tabs()
        footer, self.save_btn, self.ok_btn, self.cancel_btn = build_footer(
            self, on_save=self._save_only, on_ok=self._save_and_close, on_cancel=self._close_tab
        )
        root.addLayout(footer)

        self._connect_modified()
        self.reload()

    def _msg(self, text: str, kind: str = 'info', timeout: int = 4000) -> None:
        if self.main_window:
            self.main_window.show_message(text, kind, timeout)

    def _init_tabs(self) -> None:
        from PySide6.QtWidgets import QWidget

        tab_main = QWidget()
        lay1 = QVBoxLayout(tab_main)
        lay1.addWidget(QLabel('Тип'))
        self.type_input = QComboBox()
        self.type_input.addItem('Юридическое лицо', 'company')
        self.type_input.addItem('ИП', 'ip')
        self.type_input.addItem('Физическое лицо', 'person')
        self.type_input.currentIndexChanged.connect(self._type_changed)
        lay1.addWidget(self.type_input)

        self.inn_input = QLineEdit()
        self.inn_input.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,12}$')))
        lay1.addWidget(QLabel('ИНН'))
        lay1.addWidget(self.inn_input)

        self.kpp_input = QLineEdit()
        self.kpp_input.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,9}$')))
        lay1.addWidget(QLabel('КПП'))
        lay1.addWidget(self.kpp_input)

        self.ogrn_input = QLineEdit()
        self.ogrn_input.setValidator(QRegularExpressionValidator(QRegularExpression(r'^[A-Za-z0-9]{0,15}$')))
        lay1.addWidget(QLabel('ОГРН / ОГРНИП'))
        lay1.addWidget(self.ogrn_input)
        lay1.addStretch(1)

        tab_addr = QWidget()
        lay2 = QVBoxLayout(tab_addr)
        lay2.addWidget(QLabel('Адрес'))
        self.address_input = QLineEdit()
        lay2.addWidget(self.address_input)
        lay2.addStretch(1)

        self.tabs.addTab(tab_main, 'Реквизиты')
        self.tabs.addTab(tab_addr, 'Контакты')

    def _connect_modified(self) -> None:
        for w in (self.name_input, self.inn_input, self.kpp_input, self.ogrn_input, self.address_input):
            w.textChanged.connect(self._mark_modified)
        self.type_input.currentIndexChanged.connect(self._mark_modified)

    def _mark_modified(self) -> None:
        self.is_modified = True

    def _type_changed(self) -> None:
        is_company = self.type_input.currentData() == 'company'
        self.kpp_input.setEnabled(is_company)
        if not is_company:
            self.kpp_input.clear()

    def reload(self) -> None:
        self.organization = get_organization()
        if self.organization:
            self.name_input.setText(self.organization.name or '')
            idx = self.type_input.findData(self.organization.organization_type)
            if idx >= 0:
                self.type_input.setCurrentIndex(idx)
            self.inn_input.setText(self.organization.inn or '')
            self.kpp_input.setText(self.organization.kpp or '')
            self.ogrn_input.setText(self.organization.ogrn or '')
            self.address_input.setText(self.organization.address or '')
        else:
            self.name_input.clear()
            self.inn_input.clear()
            self.kpp_input.clear()
            self.ogrn_input.clear()
            self.address_input.clear()
            self.type_input.setCurrentIndex(0)
        self._type_changed()
        self.is_modified = False

    def _validate(self) -> bool:
        if not self.name_input.text().strip():
            self._msg('Название организации обязательно', 'error', 4000)
            return False
        if not self.inn_input.text().strip():
            self._msg('ИНН обязателен', 'error', 4000)
            return False
        return True

    def _collect(self) -> dict[str, str | None]:
        return {
            'name': self.name_input.text().strip(),
            'inn': self.inn_input.text().strip(),
            'kpp': self.kpp_input.text().strip() or None,
            'ogrn': self.ogrn_input.text().strip() or None,
            'address': self.address_input.text().strip() or None,
            'organization_type': self.type_input.currentData(),
        }

    def _save(self) -> bool:
        if not self.is_modified:
            return False
        if not self._validate():
            return False
        data = self._collect()
        try:
            if self.organization is None:
                self.organization = create_organization(data)
            else:
                self.organization = update_organization(data)
        except Exception as e:
            self._msg(f'Ошибка сохранения организации: {e}', 'error', 6000)
            return False
        self.is_modified = False
        if self.on_saved:
            self.on_saved()
        return True

    def _save_only(self) -> None:
        self._save()

    def _save_and_close(self) -> None:
        self._save()

    def _close_tab(self) -> None:
        if not confirm_close_if_modified(self, self.is_modified):
            return
        parent = self.parent()
        while parent is not None and not hasattr(parent, 'removeTab'):
            parent = parent.parent()
        if parent is not None:
            idx = parent.indexOf(self)
            if idx >= 0:
                parent.removeTab(idx)
