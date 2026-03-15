from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox
)

from services.expense_articles import (
    get_expense_article_by_id,
    create_expense_article,
    update_expense_article,
)


class ExpenseArticleForm(QDialog):
    def __init__(self, *, main_window=None, article_id: int | None = None, mode: str = "create", on_saved=None):
        super().__init__()
        self.main_window = main_window
        self.article_id = article_id
        self.mode = mode
        self.on_saved = on_saved

        self.obj = None
        self.is_modified = False

        self.setWindowTitle("Статья расходов")
        self.setFixedWidth(460)

        self._init_ui()
        if article_id is not None:
            self._load()

    def _init_ui(self):
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Наименование *"))
        self.name = QLineEdit()
        lay.addWidget(self.name)

        lay.addWidget(QLabel("Группа"))
        self.group = QLineEdit()
        lay.addWidget(self.group)

        lay.addWidget(QLabel("Примечание"))
        self.note = QLineEdit()
        lay.addWidget(self.note)

        self.active = QCheckBox("Активна")
        self.active.setChecked(True)
        lay.addWidget(self.active)

        btns = QHBoxLayout()
        self.btn_save = QPushButton("Записать")
        self.btn_ok = QPushButton("ОК")
        self.btn_cancel = QPushButton("Отмена")
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        lay.addLayout(btns)

        self.btn_save.clicked.connect(self._save_only)
        self.btn_ok.clicked.connect(self._save_and_close)
        self.btn_cancel.clicked.connect(self.reject)

        for w in (self.name, self.group, self.note):
            w.textChanged.connect(self._mark_modified)
        self.active.stateChanged.connect(self._mark_modified)

    def _mark_modified(self):
        self.is_modified = True

    def _load(self):
        self.obj = get_expense_article_by_id(self.article_id) if self.article_id is not None else None
        if not self.obj:
            return
        self.name.setText(self.obj.name)
        self.group.setText(self.obj.group or "")
        self.note.setText(self.obj.note or "")
        self.active.setChecked(bool(self.obj.is_active))

        self.is_modified = False

        if self.mode == "copy":
            self.article_id = None
            self.obj = None
            self.setWindowTitle("Копия: Статья расходов")

    def _validate(self) -> bool:
        if not self.name.text().strip():
            if self.main_window:
                self.main_window.show_message("Наименование обязательно", "error", 4000)
            return False
        return True

    def _collect(self) -> dict[str, Any]:
        return {
            "name": self.name.text().strip(),
            "group": self.group.text().strip() or None,
            "note": self.note.text().strip() or None,
            "is_active": self.active.isChecked(),
        }

    def _save(self) -> bool:
        if not self.is_modified and self.mode != "create":
            return False
        if not self._validate():
            return False

        data = self._collect()
        try:
            if self.article_id is None:
                self.article_id = create_expense_article(data)
            else:
                update_expense_article(self.article_id, data)
        except Exception as e:
            if self.main_window:
                self.main_window.show_message(str(e), "error", 7000)
            return False

        self.is_modified = False
        if self.on_saved:
            self.on_saved()
        return True

    def _save_only(self):
        if self._save() and self.main_window:
            self.main_window.show_message("Сохранено", "success", 2000)

    def _save_and_close(self):
        if self._save():
            self.accept()
