from __future__ import annotations

from typing import Callable, Any

from PySide6.QtCore import Qt, QEvent, QPoint, QObject
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QTableWidget, QMenu


class OneCTableHelper(QObject):
    """
    Универсальный помощник для QTableWidget в стиле 1С:
    - полосатые строки
    - Ctrl+A / Ctrl+R / Enter / Del
    - контекстное меню
    - быстрые действия через callbacks
    """

    def __init__(
        self,
        table: QTableWidget,
        *,
        status: Callable[[str, str, int], None],
        get_current_id: Callable[[], int | None],
        get_selected_ids: Callable[[], list[int]],
        on_open: Callable[[], None],
        on_delete: Callable[[], None],
        on_reload: Callable[[], None],
        on_select_all: Callable[[], None] | None = None,
        on_clear_selection: Callable[[], None] | None = None,
        on_restore: Callable[[], None] | None = None,
        on_delete_forever: Callable[[], None] | None = None,
        hint_text: str | None = None,
    ) -> None:
        super().__init__(table)
        self.table = table
        self.status = status

        self.get_current_id = get_current_id
        self.get_selected_ids = get_selected_ids

        self.on_open = on_open
        self.on_delete = on_delete
        self.on_reload = on_reload

        self.on_select_all = on_select_all
        self.on_clear_selection = on_clear_selection
        self.on_restore = on_restore
        self.on_delete_forever = on_delete_forever

        self.hint_text = hint_text or "Enter — открыть, Del — удалить, Ctrl+A — выделить всё, Ctrl+R — обновить"

        self._setup_table()

    def _setup_table(self) -> None:
        # визуал 1С
        self.table.setAlternatingRowColors(True)

        # горячие клавиши
        self.table.installEventFilter(self)

        # контекстное меню
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

        # подсказка
        self.status(self.hint_text, "info", 2000)

    def eventFilter(self, obj: Any, event: Any) -> bool:
        if obj is self.table and event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            key = event.key()
            mods = event.modifiers()

            if key == Qt.Key.Key_A and mods & Qt.KeyboardModifier.ControlModifier:
                if self.on_select_all:
                    self.on_select_all()
                else:
                    self.table.selectAll()
                    self.status("Выделено всё", "info", 1200)
                return True

            if key == Qt.Key.Key_R and mods & Qt.KeyboardModifier.ControlModifier:
                self.on_reload()
                return True

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.on_open()
                return True

            if key == Qt.Key.Key_Delete:
                self.on_delete()
                return True

        return super().eventFilter(obj, event)

    def _open_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self.table)

        act_open = menu.addAction("Открыть")
        act_delete = menu.addAction("Удалить")

        # опциональные действия (для архива)
        act_restore = None
        act_delete_forever = None
        if self.on_restore is not None:
            act_restore = menu.addAction("↩ Восстановить")
        if self.on_delete_forever is not None:
            act_delete_forever = menu.addAction("🗑 Удалить навсегда")

        menu.addSeparator()
        act_select_all = menu.addAction("✅ Выделить всё")
        act_clear = menu.addAction("🚫 Снять выделение")
        act_reload = menu.addAction("⟳ Обновить")

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen is None:
            return

        if chosen == act_open:
            self.on_open()
            return

        if chosen == act_delete:
            self.on_delete()
            return

        if act_restore is not None and chosen == act_restore and self.on_restore is not None:
            self.on_restore()
            return

        if act_delete_forever is not None and chosen == act_delete_forever and self.on_delete_forever is not None:
            self.on_delete_forever()
            return

        if chosen == act_select_all:
            if self.on_select_all:
                self.on_select_all()
            else:
                self.table.selectAll()
                self.status("Выделено всё", "info", 1200)
            return

        if chosen == act_clear:
            if self.on_clear_selection:
                self.on_clear_selection()
            else:
                self.table.clearSelection()
                self.status("Выделение снято", "info", 1200)
            return

        if chosen == act_reload:
            self.on_reload()
            return
