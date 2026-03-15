from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Optional

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView, QSizePolicy
)

LogicOp = Literal["AND", "OR"]

# ---- field metadata ----
@dataclass(frozen=True)
class FilterField:
    key: str                 # key used in filter spec and for mapping to model attr
    title: str               # label shown to user
    kind: Literal["str", "int", "bool", "date", "enum"] = "str"
    # for enum/bool, list of (title,value)
    choices: Optional[list[tuple[str, Any]]] = None


# ---- filter spec ----
# Group: {"type":"group","op":"AND|OR","items":[...]}
# Cond : {"type":"cond","field":"name","cmp":"contains","value":"abc"}
FilterSpec = dict[str, Any]

CMP_LABELS: list[tuple[str, str]] = [
    ("Равно", "eq"),
    ("Не равно", "neq"),
    ("Содержит", "contains"),
    ("Не содержит", "not_contains"),
    ("Начинается с", "starts"),
    ("Заканчивается на", "ends"),
    ("Больше", "gt"),
    ("Больше или равно", "gte"),
    ("Меньше", "lt"),
    ("Меньше или равно", "lte"),
    ("Пусто", "is_null"),
    ("Не пусто", "not_null"),
]

# which operators are sensible for which kinds
KIND_TO_CMPS: dict[str, set[str]] = {
    "str": {"eq", "neq", "contains", "not_contains", "starts", "ends", "is_null", "not_null"},
    "int": {"eq", "neq", "gt", "gte", "lt", "lte", "is_null", "not_null"},
    "bool": {"eq", "neq"},
    "enum": {"eq", "neq"},
    "date": {"eq", "neq", "gt", "gte", "lt", "lte", "is_null", "not_null"},
}


class UTFilterPanel(QWidget):
    """
    Фильтр как в 1С УТ: таблица условий + группы (И/ИЛИ).
    Универсальный: окна передают список полей (FilterField), а наружу выходит FilterSpec.
    """
    applied = Signal(dict)  # FilterSpec root group
    reset = Signal()

    def __init__(self, fields: list[FilterField], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fields = fields
        self._field_by_key = {f.key: f for f in fields}

        self.setObjectName("UTFilterPanel")
        self._anim: QPropertyAnimation | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header row (like "Отбор" with buttons)
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 8, 10, 8)
        hl.setSpacing(8)

        self.title = QLabel("Отбор")
        self.title.setObjectName("UTFilterTitle")

        self.btn_add_cond = QPushButton("Добавить условие")
        self.btn_add_cond.setObjectName("UTFilterAdd")

        self.btn_add_group = QPushButton("Добавить группу")
        self.btn_add_group.setObjectName("UTFilterAddGroup")

        hl.addWidget(self.title)
        hl.addStretch(1)
        hl.addWidget(self.btn_add_cond)
        hl.addWidget(self.btn_add_group)

        root.addWidget(header)

        # body frame to animate height
        self.body = QFrame()
        self.body.setObjectName("UTFilterBody")
        self.body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.body.setMaximumHeight(0)
        root.addWidget(self.body)

        bl = QVBoxLayout(self.body)
        bl.setContentsMargins(10, 8, 10, 10)
        bl.setSpacing(8)

        # root op selector
        op_row = QHBoxLayout()
        op_row.setSpacing(8)
        op_row.addWidget(QLabel("Связь условий:"))
        self.root_op = QComboBox()
        self.root_op.addItem("И", "AND")
        self.root_op.addItem("ИЛИ", "OR")
        self.root_op.setFixedWidth(110)
        op_row.addWidget(self.root_op)
        op_row.addStretch(1)
        bl.addLayout(op_row)

        # tree
        self.tree = QTreeWidget()
        self.tree.setObjectName("UTFilterTree")
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Поле", "Оператор", "Значение", ""])
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(18)
        self.tree.setAlternatingRowColors(True)
        bl.addWidget(self.tree)

        # footer buttons
        footer = QHBoxLayout()
        footer.addStretch(1)
        self.btn_apply = QPushButton("Применить")
        self.btn_apply.setObjectName("UTFilterApply")
        self.btn_reset = QPushButton("Сбросить")
        self.btn_reset.setObjectName("UTFilterReset")
        footer.addWidget(self.btn_apply)
        footer.addWidget(self.btn_reset)
        bl.addLayout(footer)

        # events
        self.btn_add_cond.clicked.connect(self.add_condition)
        self.btn_add_group.clicked.connect(self.add_group)
        self.btn_apply.clicked.connect(self._emit_applied)
        self.btn_reset.clicked.connect(self._emit_reset)

        # start with one condition
        self.add_condition()

        # expanded by default? no
        self._expanded = False

    # ---------- public API ----------
    def toggle(self) -> None:
        self.setExpanded(not self._expanded)

    def setExpanded(self, expanded: bool) -> None:
        self._expanded = expanded
        start = self.body.maximumHeight()
        end = self._content_height() if expanded else 0

        anim = QPropertyAnimation(self.body, b"maximumHeight", self)
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.start()
        self._anim = anim

    def set_filter_spec(self, spec: FilterSpec) -> None:
        self.tree.clear()
        self.root_op.setCurrentIndex(0 if spec.get("op") == "AND" else 1)
        for item in spec.get("items", []):
            self._add_item_from_spec(self.tree.invisibleRootItem(), item)

    def get_filter_spec(self) -> FilterSpec:
        return {"type": "group", "op": self.root_op.currentData(), "items": self._spec_from_parent(self.tree.invisibleRootItem())}

    def add_condition(self) -> None:
        parent = self._selected_parent_item()
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.ItemDataRole.UserRole, {"type": "cond"})
        self._init_cond_row(item)
        parent.setExpanded(True)

    def add_group(self) -> None:
        parent = self._selected_parent_item()
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.ItemDataRole.UserRole, {"type": "group"})
        item.setText(0, "Группа")
        # operator widget for group
        cb = QComboBox()
        cb.addItem("И", "AND")
        cb.addItem("ИЛИ", "OR")
        cb.setFixedWidth(110)
        self.tree.setItemWidget(item, 1, cb)

        # remove btn
        rm = QPushButton("✕")
        rm.setObjectName("UTFilterRemove")
        rm.setFixedWidth(26)
        rm.clicked.connect(lambda: self._remove_item(item))
        self.tree.setItemWidget(item, 3, rm)

        parent.setExpanded(True)

    def add_condition_from_value(self, field_key: str, cmp_key: str, value: Any) -> None:
        # convenience for ПКМ "Отбор по значению"
        self.setExpanded(True)
        self.add_condition()
        sel = self.tree.currentItem()
        if sel is None:
            return
        self._set_cond_widgets(sel, field_key, cmp_key, value)

    # ---------- internal ----------
    def _content_height(self) -> int:
        # heuristic: header + tree + footer
        return 320

    def _selected_parent_item(self) -> QTreeWidgetItem:
        cur = self.tree.currentItem()
        if cur is None:
            return self.tree.invisibleRootItem()
        kind = (cur.data(0, Qt.ItemDataRole.UserRole) or {}).get("type")
        if kind == "group":
            return cur
        # for condition: parent group/root
        return cur.parent() or self.tree.invisibleRootItem()

    def _remove_item(self, item: QTreeWidgetItem) -> None:
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.removeChild(item)
        if self.tree.topLevelItemCount() == 0:
            self.add_condition()

    def _emit_applied(self) -> None:
        self.applied.emit(self.get_filter_spec())

    def _emit_reset(self) -> None:
        self.tree.clear()
        self.root_op.setCurrentIndex(0)
        self.add_condition()
        self.reset.emit()

    # ----- spec conversions -----
    def _spec_from_parent(self, parent: QTreeWidgetItem) -> list[FilterSpec]:
        items: list[FilterSpec] = []
        for i in range(parent.childCount()):
            it = parent.child(i)
            meta = it.data(0, Qt.ItemDataRole.UserRole) or {}
            t = meta.get("type")
            if t == "group":
                opw = self.tree.itemWidget(it, 1)
                op = opw.currentData() if isinstance(opw, QComboBox) else "AND"
                items.append({"type": "group", "op": op, "items": self._spec_from_parent(it)})
            else:
                items.append(self._cond_spec_from_item(it))
        return items

    def _cond_spec_from_item(self, item: QTreeWidgetItem) -> FilterSpec:
        fw = self.tree.itemWidget(item, 0)
        cw = self.tree.itemWidget(item, 1)
        vw = self.tree.itemWidget(item, 2)

        field_key = fw.currentData() if isinstance(fw, QComboBox) else None
        cmp_key = cw.currentData() if isinstance(cw, QComboBox) else None
        value: Any = None

        if isinstance(vw, QComboBox):
            value = vw.currentData()
        elif isinstance(vw, QLineEdit):
            value = vw.text().strip() or None

        return {"type": "cond", "field": field_key, "cmp": cmp_key, "value": value}

    def _add_item_from_spec(self, parent: QTreeWidgetItem, spec: FilterSpec) -> None:
        t = spec.get("type")
        if t == "group":
            it = QTreeWidgetItem(parent)
            it.setData(0, Qt.ItemDataRole.UserRole, {"type": "group"})
            it.setText(0, "Группа")
            cb = QComboBox()
            cb.addItem("И", "AND")
            cb.addItem("ИЛИ", "OR")
            cb.setCurrentIndex(0 if spec.get("op") == "AND" else 1)
            cb.setFixedWidth(110)
            self.tree.setItemWidget(it, 1, cb)
            rm = QPushButton("✕")
            rm.setObjectName("UTFilterRemove")
            rm.setFixedWidth(26)
            rm.clicked.connect(lambda: self._remove_item(it))
            self.tree.setItemWidget(it, 3, rm)
            for ch in spec.get("items", []):
                self._add_item_from_spec(it, ch)
        else:
            it = QTreeWidgetItem(parent)
            it.setData(0, Qt.ItemDataRole.UserRole, {"type": "cond"})
            self._init_cond_row(it)
            self._set_cond_widgets(it, spec.get("field"), spec.get("cmp"), spec.get("value"))

    # ----- widgets for condition row -----
    def _init_cond_row(self, item: QTreeWidgetItem) -> None:
        field_cb = QComboBox()
        for f in self._fields:
            field_cb.addItem(f.title, f.key)
        field_cb.currentIndexChanged.connect(lambda _=0, it=item: self._on_field_changed(it))
        self.tree.setItemWidget(item, 0, field_cb)

        cmp_cb = QComboBox()
        self.tree.setItemWidget(item, 1, cmp_cb)

        value_widget = QLineEdit()
        self.tree.setItemWidget(item, 2, value_widget)

        rm = QPushButton("✕")
        rm.setObjectName("UTFilterRemove")
        rm.setFixedWidth(26)
        rm.clicked.connect(lambda: self._remove_item(item))
        self.tree.setItemWidget(item, 3, rm)

        # init operators based on first field
        self._on_field_changed(item)

    def _on_field_changed(self, item: QTreeWidgetItem) -> None:
        field_cb = self.tree.itemWidget(item, 0)
        cmp_cb = self.tree.itemWidget(item, 1)
        if not isinstance(field_cb, QComboBox) or not isinstance(cmp_cb, QComboBox):
            return

        key = field_cb.currentData()
        f = self._field_by_key.get(key)
        kind = f.kind if f else "str"

        cmp_cb.blockSignals(True)
        cmp_cb.clear()
        allowed = KIND_TO_CMPS.get(kind, KIND_TO_CMPS["str"])
        for title, ck in CMP_LABELS:
            if ck in allowed:
                cmp_cb.addItem(title, ck)
        # default
        if kind in ("bool", "enum"):
            # better default: eq
            idx = cmp_cb.findData("eq")
            if idx >= 0:
                cmp_cb.setCurrentIndex(idx)
        else:
            idx = cmp_cb.findData("contains")
            if idx >= 0:
                cmp_cb.setCurrentIndex(idx)
        cmp_cb.blockSignals(False)

        # value widget depends on kind
        old = self.tree.itemWidget(item, 2)
        if old is not None:
            old.deleteLater()

        if f and f.kind in ("bool", "enum") and f.choices:
            val_cb = QComboBox()
            for title, v in f.choices:
                val_cb.addItem(title, v)
            self.tree.setItemWidget(item, 2, val_cb)
        else:
            val = QLineEdit()
            val.setPlaceholderText("Значение")
            self.tree.setItemWidget(item, 2, val)

    def _set_cond_widgets(self, item: QTreeWidgetItem, field_key: Any, cmp_key: Any, value: Any) -> None:
        fw = self.tree.itemWidget(item, 0)
        if isinstance(fw, QComboBox) and field_key is not None:
            idx = fw.findData(field_key)
            if idx >= 0:
                fw.setCurrentIndex(idx)

        # field change may recreate widgets
        self._on_field_changed(item)

        cw = self.tree.itemWidget(item, 1)
        if isinstance(cw, QComboBox) and cmp_key is not None:
            idx = cw.findData(cmp_key)
            if idx >= 0:
                cw.setCurrentIndex(idx)

        vw = self.tree.itemWidget(item, 2)
        if isinstance(vw, QComboBox):
            idx = vw.findData(value)
            if idx >= 0:
                vw.setCurrentIndex(idx)
        elif isinstance(vw, QLineEdit):
            vw.setText("" if value is None else str(value))
