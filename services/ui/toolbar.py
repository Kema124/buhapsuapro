from __future__ import annotations

from PySide6.QtWidgets import QToolBar, QWidget, QSizePolicy
from PySide6.QtGui import QAction
from PySide6.QtCore import QSize

from ui.assets import load_icon


def create_toolbar(parent):
    """Единый тёмный тулбар как в 1С.

    Возвращает toolbar и actions (для main_window).
    """
    toolbar = QToolBar()
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setIconSize(QSize(20, 20))

    # тулбар всегда тёмный -> иконки светлые
    c = "#ffffff"

    directories_action = QAction(load_icon("open.svg", color=c), "Справочники", parent)
    documents_action = QAction(load_icon("documents.svg", color=c), "Документы", parent)
    archive_action = QAction(load_icon("archive.svg", color=c), "Архив", parent)

    refresh_action = QAction(load_icon("refresh.svg", color=c), "Обновить", parent)
    settings_action = QAction(load_icon("settings.svg", color=c), "Настройки", parent)
    back_action = QAction(load_icon("back.svg", color=c), "Базы", parent)

    toolbar.addAction(documents_action)
    toolbar.addAction(directories_action)
    toolbar.addAction(archive_action)
    toolbar.addAction(refresh_action)
    toolbar.addSeparator()
    toolbar.addAction(settings_action)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    toolbar.addWidget(spacer)

    toolbar.addAction(back_action)

    return (
        toolbar,
        directories_action,
        documents_action,
        archive_action,
        settings_action,
        refresh_action,
        back_action,
    )
