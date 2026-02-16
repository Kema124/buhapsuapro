from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from PySide6.QtWidgets import QTabWidget, QWidget, QMessageBox


@dataclass(frozen=True)
class TabSpec:
    key: str
    title: str
    factory: Callable[[], QWidget]
    singleton: bool = True


class TabManager:
    def __init__(self, tabs: QTabWidget, main_window: QWidget):
        self.tabs = tabs
        self.main_window = main_window
        self._specs: dict[str, TabSpec] = {}
        self._opened: dict[str, QWidget] = {}

        self.tabs.tabCloseRequested.connect(self.close)

    def register(self, spec: TabSpec) -> None:
        self._specs[spec.key] = spec

    def open(self, key: str) -> QWidget:
        if key in self._opened:
            idx = self.tabs.indexOf(self._opened[key])
            if idx >= 0:
                self.tabs.setCurrentIndex(idx)
                return self._opened[key]

        spec = self._specs[key]
        widget = spec.factory()
        self._opened[key] = widget
        idx = self.tabs.addTab(widget, spec.title)
        self.tabs.setCurrentIndex(idx)
        return widget

    def close(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if not widget:
            return

        self.tabs.removeTab(index)
        widget.deleteLater()

        for k, v in list(self._opened.items()):
            if v == widget:
                self._opened.pop(k)

    def close_by_key(self, key: str) -> None:
        if key not in self._opened:
            return
        widget = self._opened[key]
        idx = self.tabs.indexOf(widget)
        if idx >= 0:
            self.close(idx)
