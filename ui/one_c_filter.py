from __future__ import annotations

"""Единый фильтр в стиле 1С (Управление торговлей).

Цель этого виджета — дать привычный UX: "Отбор" как набор условий
(Поле + Оператор + Значение), с возможностью добавлять/удалять строки.

ВАЖНО: чтобы не ломать текущую архитектуру проекта, панель остаётся
совместимой с прежним API:
  - FilterField
  - OneCFilterPanel.applied (Signal(dict))
  - OneCFilterPanel.reset (Signal())

Сигнал applied эмитит простой dict вида {key: value | None}, чтобы
существующие service.filter_* могли работать без изменений.
Для совместимости мы не поддерживаем несколько условий на одно поле:
при добавлении новой строки список полей исключает уже выбранные.
"""

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QToolButton,
    QSizePolicy,
)


@dataclass(frozen=True)
class FilterField:
    key: str
    label: str
    kind: str = "text"  # "text" | "combo"
    placeholder: str = ""
    # for combo: list of (title, data)
    items: list[tuple[str, Any]] | None = None


class _ConditionRow(QWidget):
    """Одна строка условия отбора."""

    removed = Signal(object)  # emits self
    changed = Signal()

    def __init__(self, fields: list[FilterField]) -> None:
        super().__init__()
        self._all_fields = fields

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.field_cb = QComboBox()
        self.field_cb.setObjectName("FilterCondField")
        self.field_cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.op_cb = QComboBox()
        self.op_cb.setObjectName("FilterCondOp")
        self.op_cb.setFixedWidth(120)

        self.value_edit = QLineEdit()
        self.value_edit.setObjectName("FilterCondValue")
        self.value_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.value_combo = QComboBox()
        self.value_combo.setObjectName("FilterCondValue")
        self.value_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.value_combo.hide()

        self.btn_remove = QToolButton()
        self.btn_remove.setObjectName("FilterCondRemove")
        self.btn_remove.setText("✕")
        self.btn_remove.setToolTip("Удалить условие")

        layout.addWidget(self.field_cb)
        layout.addWidget(self.op_cb)
        layout.addWidget(self.value_edit, 1)
        layout.addWidget(self.value_combo, 1)
        layout.addWidget(self.btn_remove)

        self.btn_remove.clicked.connect(lambda: self.removed.emit(self))
        self.field_cb.currentIndexChanged.connect(self._field_changed)
        self.op_cb.currentIndexChanged.connect(lambda *_: self.changed.emit())
        self.value_edit.textChanged.connect(lambda *_: self.changed.emit())
        self.value_combo.currentIndexChanged.connect(lambda *_: self.changed.emit())

        self._rebuild_fields()
        self._field_changed()

    def _rebuild_fields(self, *, allowed_keys: set[str] | None = None) -> None:
        """Пересобирает список полей. Можно ограничить allowed_keys."""
        cur_key = self.current_key()
        self.field_cb.blockSignals(True)
        self.field_cb.clear()
        for f in self._all_fields:
            if allowed_keys is not None and f.key not in allowed_keys:
                continue
            self.field_cb.addItem(f.label, f.key)
        # восстановить выбор
        if cur_key is not None:
            idx = self.field_cb.findData(cur_key)
            if idx >= 0:
                self.field_cb.setCurrentIndex(idx)
        self.field_cb.blockSignals(False)

    def set_allowed_keys(self, allowed_keys: set[str]) -> None:
        self._rebuild_fields(allowed_keys=allowed_keys)

    def current_key(self) -> str | None:
        v = self.field_cb.currentData()
        return str(v) if v is not None else None

    def _spec(self) -> FilterField | None:
        key = self.current_key()
        if key is None:
            return None
        for f in self._all_fields:
            if f.key == key:
                return f
        return None

    def _field_changed(self) -> None:
        spec = self._spec()

        # оператор под текущий тип
        self.op_cb.blockSignals(True)
        self.op_cb.clear()
        if spec is None:
            self.op_cb.addItem("Содержит", "contains")
        else:
            if spec.kind == "combo":
                self.op_cb.addItem("Равно", "eq")
            else:
                # Совместимость с текущими сервисами: используем contains
                self.op_cb.addItem("Содержит", "contains")
        self.op_cb.blockSignals(False)

        # редактор значения
        if spec is not None and spec.kind == "combo":
            self.value_edit.hide()
            self.value_combo.show()
            self.value_combo.blockSignals(True)
            self.value_combo.clear()
            items = spec.items or []
            for title, data in items:
                self.value_combo.addItem(title, data)
            self.value_combo.blockSignals(False)
        else:
            self.value_combo.hide()
            self.value_edit.show()
            self.value_edit.setPlaceholderText(spec.placeholder if spec else "")

        self.changed.emit()

    def value(self) -> Any:
        spec = self._spec()
        if spec is not None and spec.kind == "combo":
            return self.value_combo.currentData()
        text = self.value_edit.text().strip()
        return text or None

    def clear_value(self) -> None:
        spec = self._spec()
        if spec is not None and spec.kind == "combo":
            self.value_combo.setCurrentIndex(0)
        else:
            self.value_edit.clear()


class OneCFilterPanel(QWidget):
    """Панель "Отбор" (как в 1С:УТ).

    Использование:
        panel = OneCFilterPanel([FilterField(...), ...])
        panel.applied.connect(lambda filters: ...)
        panel.reset.connect(lambda: ...)

    Внешняя кнопка "Фильтр" управляет видимостью панели.
    """

    applied = Signal(dict)
    reset = Signal()

    def __init__(self, fields: list[FilterField]) -> None:
        super().__init__()
        self._fields = fields
        self._rows: list[_ConditionRow] = []

        self._build()
        self._add_row()  # по умолчанию одна строка

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # Заголовок "Отбор" + кнопка добавить
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        title = QLabel("Отбор")
        title.setObjectName("FilterTitle")

        header.addWidget(title)
        header.addStretch(1)

        self.btn_add = QPushButton("Добавить")
        self.btn_add.setObjectName("FilterAdd")
        header.addWidget(self.btn_add)

        root.addLayout(header)

        self.rows_host = QVBoxLayout()
        self.rows_host.setContentsMargins(0, 0, 0, 0)
        self.rows_host.setSpacing(6)
        root.addLayout(self.rows_host)

        # Кнопки
        footer = QHBoxLayout()
        footer.addStretch(1)

        self.btn_apply = QPushButton("Применить")
        self.btn_reset = QPushButton("Сбросить")
        self.btn_apply.setObjectName("FilterApply")
        self.btn_reset.setObjectName("FilterReset")

        footer.addWidget(self.btn_apply)
        footer.addWidget(self.btn_reset)
        root.addLayout(footer)

        self.btn_add.clicked.connect(self._add_row)
        self.btn_apply.clicked.connect(self._emit_applied)
        self.btn_reset.clicked.connect(self._do_reset)

    # ----------------- public API -----------------

    def values(self) -> dict[str, Any]:
        """Совместимый вывод {key: value|None}."""
        out: dict[str, Any] = {}
        for r in self._rows:
            key = r.current_key()
            if not key:
                continue
            out[key] = r.value()
        return out

    def set_values(self, values: dict[str, Any]) -> None:
        # Пересоздаём строки по values, сохраняя совместимость.
        self._clear_rows()
        keys = [k for k, v in values.items() if v is not None]
        if not keys:
            self._add_row()
            return
        for k in keys:
            row = self._add_row(select_key=k)
            # заполнить значение
            v = values.get(k)
            if isinstance(row.value_combo, QComboBox) and row.value_combo.isVisible():
                idx = row.value_combo.findData(v)
                if idx >= 0:
                    row.value_combo.setCurrentIndex(idx)
            else:
                row.value_edit.setText("" if v is None else str(v))

    def clear(self) -> None:
        for r in self._rows:
            r.clear_value()

    # ----------------- internals -----------------

    def _allowed_keys_for(self, row: _ConditionRow) -> set[str]:
        used = {r.current_key() for r in self._rows if r is not row}
        used.discard(None)
        all_keys = {f.key for f in self._fields}
        return all_keys - set(used)  # type: ignore[arg-type]

    def _sync_allowed_keys(self) -> None:
        for r in self._rows:
            r.set_allowed_keys(self._allowed_keys_for(r))

    def _add_row(self, *, select_key: str | None = None) -> _ConditionRow:
        row = _ConditionRow(self._fields)
        self._rows.append(row)
        self.rows_host.addWidget(row)

        row.removed.connect(self._remove_row)
        row.changed.connect(self._sync_allowed_keys)

        self._sync_allowed_keys()

        if select_key is not None:
            idx = row.field_cb.findData(select_key)
            if idx >= 0:
                row.field_cb.setCurrentIndex(idx)

        return row

    def _remove_row(self, row_obj: object) -> None:
        row = row_obj if isinstance(row_obj, _ConditionRow) else None
        if row is None:
            return
        if row in self._rows:
            self._rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        if not self._rows:
            self._add_row()
        self._sync_allowed_keys()

    def _clear_rows(self) -> None:
        for r in list(self._rows):
            self._remove_row(r)

    def _emit_applied(self) -> None:
        self.applied.emit(self.values())

    def _do_reset(self) -> None:
        self._clear_rows()
        self._add_row()
        self.reset.emit()
