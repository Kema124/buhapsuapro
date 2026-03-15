from __future__ import annotations

from typing import Literal

from PySide6.QtWidgets import QStatusBar

MsgType = Literal["info", "success", "warning", "error"]


class StatusMessenger:
    def __init__(self, status_bar: QStatusBar) -> None:
        self._bar = status_bar

    def show(self, message: str, msg_type: MsgType = "info", timeout: int = 5000) -> None:
        if msg_type == "success":
            color = "#2e7d32"
        elif msg_type == "error":
            color = "#c62828"
        elif msg_type == "warning":
            color = "#f9a825"
        else:
            color = "#1976d2"

        self._bar.setStyleSheet(
            f"""
            QStatusBar {{
                background-color: {color};
                color: white;
                font-weight: bold;
            }}
            """
        )
        self._bar.showMessage(message, timeout)
