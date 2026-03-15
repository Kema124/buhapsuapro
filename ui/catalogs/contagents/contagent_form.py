from __future__ import annotations

import json
from datetime import date
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator, QDoubleValidator
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QMessageBox, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QAbstractItemView
)

from services.contagents import get_contagent_by_id, create_contagent, update_contagent
from services.contracts import get_contracts_by_contagent, soft_delete_contract
from services.contagent_bank_accounts import (
    get_accounts_by_contagent, delete_bank_account
)

from ui.address_dialog import AddressDialog, assemble_address
from ui.contract_form import ContractForm
from ui.contagent_bank_account_form import ContagentBankAccountForm


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

        # address parts cached (for edit dialog)
        self.legal_parts: dict[str, Any] | None = None
        self.factual_parts: dict[str, Any] | None = None

        self.setWindowTitle("Контрагент")
        self.setMinimumSize(720, 520)

        self._init_ui()

        if self.contagent_id is not None:
            self._load_data()

    # ==========================
    # UI
    # ==========================

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)

        # Наименование сверху
        root.addWidget(QLabel("Наименование *"))
        self.name_input = QLineEdit()
        root.addWidget(self.name_input)

        # Табы
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.tab_main = QWidget()
        self.tab_contacts = QWidget()
        self.tab_accounts_contracts = QWidget()

        self.tabs.addTab(self.tab_main, "Реквизиты")
        self.tabs.addTab(self.tab_contacts, "Контакты")
        self.tabs.addTab(self.tab_accounts_contracts, "Счета и договоры")

        self._build_tab_main()
        self._build_tab_contacts()
        self._build_tab_accounts_contracts()

        # Активность / удаление
        flags = QHBoxLayout()
        self.active_checkbox = QCheckBox("Активен")
        self.active_checkbox.setChecked(True)
        self.deleted_checkbox = QCheckBox("Удалён")
        self.deleted_checkbox.setChecked(False)
        flags.addWidget(self.active_checkbox)
        flags.addWidget(self.deleted_checkbox)
        flags.addStretch(1)
        root.addLayout(flags)

        # Кнопки
        btns = QHBoxLayout()
        self.save_btn = QPushButton("Записать")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        root.addLayout(btns)

        self.save_btn.clicked.connect(self._save_only)
        self.ok_btn.clicked.connect(self._ok_clicked)
        self.cancel_btn.clicked.connect(self.close_form)

        # modified tracking
        self.name_input.textChanged.connect(self._mark_modified)
        self.role_input.currentIndexChanged.connect(self._mark_modified)
        self.org_type_input.currentIndexChanged.connect(self._mark_modified)
        self.inn_input.textChanged.connect(self._mark_modified)
        self.kpp_input.textChanged.connect(self._mark_modified)

        self.phone_input.textChanged.connect(self._mark_modified)
        self.legal_address_input.textChanged.connect(self._mark_modified)
        self.factual_address_input.textChanged.connect(self._mark_modified)
        self.geo_lat_input.textChanged.connect(self._mark_modified)
        self.geo_lon_input.textChanged.connect(self._mark_modified)

        self.active_checkbox.stateChanged.connect(self._mark_modified)
        self.deleted_checkbox.stateChanged.connect(self._mark_modified)

        self._org_type_changed()

    def _build_tab_main(self) -> None:
        layout = QVBoxLayout(self.tab_main)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Роль/Тип"))
        self.role_input = QComboBox()
        self.role_input.addItem("Покупатель", "buyer")
        self.role_input.addItem("Поставщик", "supplier")
        self.role_input.addItem("Покупатель и поставщик", "both")
        row1.addWidget(self.role_input)

        self.org_type_input = QComboBox()
        self.org_type_input.addItem("Юридическое лицо", "company")
        self.org_type_input.addItem("ИП", "ip")
        self.org_type_input.addItem("Физическое лицо", "person")
        self.org_type_input.currentIndexChanged.connect(self._org_type_changed)
        row1.addWidget(self.org_type_input)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("ИНН"))
        self.inn_input = QLineEdit()
        self.inn_input.setValidator(QIntValidator())
        self.inn_input.setMaxLength(8)
        row2.addWidget(self.inn_input)

        row2.addWidget(QLabel("КПП"))
        self.kpp_input = QLineEdit()
        self.kpp_input.setValidator(QIntValidator())
        self.kpp_input.setMaxLength(9)
        row2.addWidget(self.kpp_input)

        layout.addLayout(row2)
        layout.addStretch(1)

    def _build_tab_contacts(self) -> None:
        layout = QVBoxLayout(self.tab_contacts)

        # Адреса (строка + кнопка "...")
        def addr_row(title: str):
            r = QHBoxLayout()
            r.addWidget(QLabel(title))
            le = QLineEdit()
            le.setReadOnly(True)
            btn = QPushButton("...")
            btn.setFixedWidth(40)
            r.addWidget(le, 1)
            r.addWidget(btn)
            return r, le, btn

        r1, self.legal_address_input, self.legal_btn = addr_row("Адрес юридический")
        layout.addLayout(r1)
        r2, self.factual_address_input, self.factual_btn = addr_row("Адрес фактический")
        layout.addLayout(r2)

        self.legal_btn.clicked.connect(self._edit_legal_address)
        self.factual_btn.clicked.connect(self._edit_factual_address)

        # Телефон + координаты
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Телефон"))
        self.phone_input = QLineEdit()
        r3.addWidget(self.phone_input, 1)
        layout.addLayout(r3)

        r4 = QHBoxLayout()
        r4.addWidget(QLabel("Географ. широта"))
        self.geo_lat_input = QLineEdit()
        self.geo_lat_input.setValidator(QDoubleValidator())
        r4.addWidget(self.geo_lat_input)

        r4.addWidget(QLabel("Долгота"))
        self.geo_lon_input = QLineEdit()
        self.geo_lon_input.setValidator(QDoubleValidator())
        r4.addWidget(self.geo_lon_input)
        layout.addLayout(r4)

        layout.addStretch(1)

    def _build_tab_accounts_contracts(self) -> None:
        layout = QVBoxLayout(self.tab_accounts_contracts)

        # --- банковские счета ---
        layout.addWidget(QLabel("Банковские счета"))

        self.bank_table = QTableWidget(0, 4)
        self.bank_table.setHorizontalHeaderLabels(["Банк", "Номер счёта", "Валюта", "Примечание"])
        self.bank_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bank_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bank_table.setAlternatingRowColors(True)
        layout.addWidget(self.bank_table)

        bank_btns = QHBoxLayout()
        self.btn_bank_add = QPushButton("+")
        self.btn_bank_del = QPushButton("−")
        bank_btns.addWidget(self.btn_bank_add)
        bank_btns.addWidget(self.btn_bank_del)
        bank_btns.addStretch(1)
        layout.addLayout(bank_btns)

        self.btn_bank_add.clicked.connect(self._bank_add)
        self.btn_bank_del.clicked.connect(self._bank_delete)

        # --- договоры ---
        layout.addWidget(QLabel("Договоры"))

        self.contract_table = QTableWidget(0, 4)
        self.contract_table.setHorizontalHeaderLabels(["Номер", "Дата", "Сумма", "Статус"])
        self.contract_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.contract_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)
        layout.addWidget(self.contract_table)

        contract_btns = QHBoxLayout()
        self.btn_contract_add = QPushButton("+")
        self.btn_contract_del = QPushButton("−")
        contract_btns.addWidget(self.btn_contract_add)
        contract_btns.addWidget(self.btn_contract_del)
        contract_btns.addStretch(1)
        layout.addLayout(contract_btns)

        self.btn_contract_add.clicked.connect(self._contract_add)
        self.btn_contract_del.clicked.connect(self._contract_delete)

        layout.addStretch(1)

    # ==========================
    # Helpers
    # ==========================

    def _mark_modified(self) -> None:
        self.is_modified = True

    def _org_type_changed(self) -> None:
        is_company = self.org_type_input.currentData() == "company"
        self.kpp_input.setEnabled(bool(is_company))
        if not is_company:
            self.kpp_input.clear()

    def _status(self, msg: str, t: str = "info") -> None:
        if self.main_window is not None:
            self.main_window.show_message(msg, t, 5000)
        else:
            QMessageBox.warning(self, "Сообщение", msg)

    # ==========================
    # Address editing
    # ==========================

    def _edit_legal_address(self) -> None:
        dlg = AddressDialog("Юридический адрес", self.legal_parts, self)
        if dlg.exec() == QDialog.Accepted:
            self.legal_parts = dlg.get_parts()
            self.legal_address_input.setText(assemble_address(self.legal_parts))
            self._mark_modified()

    def _edit_factual_address(self) -> None:
        dlg = AddressDialog("Фактический адрес", self.factual_parts, self)
        if dlg.exec() == QDialog.Accepted:
            self.factual_parts = dlg.get_parts()
            self.factual_address_input.setText(assemble_address(self.factual_parts))
            self._mark_modified()

    # ==========================
    # Tables: bank accounts / contracts
    # ==========================

    def _bank_add(self) -> None:
        if self.contagent_id is None:
            if not self._save():
                return
        assert self.contagent_id is not None
        dlg = ContagentBankAccountForm(int(self.contagent_id), None, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_bank_accounts()

    def _bank_delete(self) -> None:
        row = self.bank_table.currentRow()
        if row < 0:
            return
        item = self.bank_table.item(row, 0)
        if item is None:
            return
        account_id = item.data(Qt.ItemDataRole.UserRole)
        if account_id is None:
            return
        try:
            delete_bank_account(int(account_id))
        except Exception as e:
            self._status(str(e), "error")
            return
        self._load_bank_accounts()

    def _contract_add(self) -> None:
        if self.contagent_id is None:
            if not self._save():
                return
        assert self.contagent_id is not None
        dlg = ContractForm(mode="create", contagent_id=int(self.contagent_id), main_window=self.main_window)
        if dlg.exec() == QDialog.Accepted:
            self._load_contracts()

    def _contract_delete(self) -> None:
        row = self.contract_table.currentRow()
        if row < 0:
            return
        item = self.contract_table.item(row, 0)
        if item is None:
            return
        contract_id = item.data(Qt.ItemDataRole.UserRole)
        if contract_id is None:
            return
        try:
            soft_delete_contract(int(contract_id))
        except Exception as e:
            self._status(str(e), "error")
            return
        self._load_contracts()

    def _load_bank_accounts(self) -> None:
        self.bank_table.setRowCount(0)
        if self.contagent_id is None:
            return
        try:
            items = get_accounts_by_contagent(int(self.contagent_id))
        except Exception:
            items = []
        for a in items:
            r = self.bank_table.rowCount()
            self.bank_table.insertRow(r)
            bank_name = getattr(a.bank, "name", "") if getattr(a, "bank", None) is not None else ""
            it0 = QTableWidgetItem(bank_name)
            it0.setData(Qt.ItemDataRole.UserRole, int(a.id))
            self.bank_table.setItem(r, 0, it0)
            self.bank_table.setItem(r, 1, QTableWidgetItem(a.account_number or ""))
            self.bank_table.setItem(r, 2, QTableWidgetItem(a.currency or ""))
            self.bank_table.setItem(r, 3, QTableWidgetItem(a.note or ""))

        self.bank_table.resizeColumnsToContents()

    def _load_contracts(self) -> None:
        self.contract_table.setRowCount(0)
        if self.contagent_id is None:
            return
        try:
            items = get_contracts_by_contagent(int(self.contagent_id))
        except Exception:
            items = []
        for c in items:
            r = self.contract_table.rowCount()
            self.contract_table.insertRow(r)

            it0 = QTableWidgetItem(c.number or "")
            it0.setData(Qt.ItemDataRole.UserRole, int(c.id))
            self.contract_table.setItem(r, 0, it0)

            d = ""
            if c.date:
                d = c.date.strftime("%d.%m.%Y")
            self.contract_table.setItem(r, 1, QTableWidgetItem(d))

            self.contract_table.setItem(r, 2, QTableWidgetItem("" if c.sum is None else str(c.sum)))

            self.contract_table.setItem(r, 3, QTableWidgetItem(c.status or ""))

        self.contract_table.resizeColumnsToContents()

    # ==========================
    # Load / Save
    # ==========================

    def _load_data(self) -> None:
        if self.contagent_id is None:
            return
        self.contagent = get_contagent_by_id(self.contagent_id)
        if not self.contagent:
            return

        self.name_input.setText(self.contagent.name or "")
        self.role_input.setCurrentIndex(self.role_input.findData(self.contagent.role))
        self.org_type_input.setCurrentIndex(self.org_type_input.findData(self.contagent.organization_type))

        self.inn_input.setText(self.contagent.inn or "")
        self.kpp_input.setText(self.contagent.kpp or "")

        # contacts
        # legacy fallback
        legal = getattr(self.contagent, "legal_address", None) or ""
        factual = getattr(self.contagent, "factual_address", None) or ""
        legacy = getattr(self.contagent, "address", None) or ""

        if not legal and legacy:
            legal = legacy

        self.legal_address_input.setText(legal)
        self.factual_address_input.setText(factual)

        # parse json parts if present
        self.legal_parts = self._safe_json(getattr(self.contagent, "legal_address_json", None))
        self.factual_parts = self._safe_json(getattr(self.contagent, "factual_address_json", None))

        self.phone_input.setText(getattr(self.contagent, "phone", None) or "")
        self.geo_lat_input.setText(getattr(self.contagent, "geo_lat", None) or "")
        self.geo_lon_input.setText(getattr(self.contagent, "geo_lon", None) or "")

        self.active_checkbox.setChecked(bool(self.contagent.is_active))
        self.deleted_checkbox.setChecked(bool(self.contagent.is_deleted))

        # tables
        self._load_bank_accounts()
        self._load_contracts()

        self.is_modified = False

    def _safe_json(self, s: Any) -> dict[str, Any] | None:
        try:
            if not s:
                return None
            return json.loads(s)
        except Exception:
            return None

    def _validate(self) -> bool:
        name = (self.name_input.text() or "").strip()
        if not name:
            self._status("Наименование обязательно", "error")
            return False

        inn = (self.inn_input.text() or "").strip()
        kpp = (self.kpp_input.text() or "").strip()

        if inn and len(inn) != 8:
            self._status("ИНН должен содержать 8 цифр", "error")
            return False
        if kpp and len(kpp) != 9 and self.kpp_input.isEnabled():
            self._status("КПП должен содержать 9 цифр", "error")
            return False

        return True

    def _collect_data(self) -> dict[str, Any]:
        legal = (self.legal_address_input.text() or "").strip() or None
        factual = (self.factual_address_input.text() or "").strip() or None

        return {
            "name": (self.name_input.text() or "").strip(),
            "role": self.role_input.currentData(),
            "organization_type": self.org_type_input.currentData(),
            "inn": (self.inn_input.text() or "").strip() or None,
            "kpp": (self.kpp_input.text() or "").strip() or None,
            "legal_address": legal,
            "legal_address_json": json.dumps(self.legal_parts, ensure_ascii=False) if self.legal_parts else None,
            "factual_address": factual,
            "factual_address_json": json.dumps(self.factual_parts, ensure_ascii=False) if self.factual_parts else None,
            "phone": (self.phone_input.text() or "").strip() or None,
            "geo_lat": (self.geo_lat_input.text() or "").strip() or None,
            "geo_lon": (self.geo_lon_input.text() or "").strip() or None,
            "is_active": bool(self.active_checkbox.isChecked()),
            "is_deleted": bool(self.deleted_checkbox.isChecked()),
        }

    def _save(self) -> bool:
        if self.mode == "edit" and not self.is_modified:
            return True

        if not self._validate():
            return False

        data = self._collect_data()

        try:
            if self.mode == "edit" and self.contagent_id is not None:
                update_contagent(int(self.contagent_id), data)
                saved_id = int(self.contagent_id)
            else:
                saved_id = int(create_contagent(data))
                self.contagent_id = saved_id
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
