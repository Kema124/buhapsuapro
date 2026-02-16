from __future__ import annotations

from PySide6.QtWidgets import QToolBar, QWidget, QHBoxLayout
from PySide6.QtGui import QAction
from ui.assets import load_icon


def create_toolbar(parent):
    toolbar = QToolBar()
    toolbar.setMovable(False)
    toolbar.setFloatable(False)

    # toolbar всегда тёмный -> иконки всегда светлые
    c = "#ffffff"

    org_action = QAction(load_icon("organization.svg", color=c, size=20), "Организация", parent)
    contagents_action = QAction(load_icon("users.svg", color=c, size=20), "Контрагенты", parent)
    archive_action = QAction(load_icon("archive.svg", color=c, size=20), "Архив", parent)
    documents_action = QAction(load_icon("documents.svg", color=c, size=20), "Документы", parent)
    settings_action = QAction(load_icon("settings.svg", color=c, size=20), "Настройки", parent)
    refresh_action = QAction(load_icon("refresh.svg", color=c, size=20), "Обновить", parent)
    back_action = QAction(load_icon("back.svg", color=c, size=20), "Базы", parent)

    toolbar.addAction(documents_action)
    toolbar.addAction(contagents_action)
    toolbar.addAction(archive_action)
    toolbar.addAction(org_action)
    toolbar.addAction(refresh_action)
    toolbar.addSeparator()
    toolbar.addAction(settings_action)

    spacer = QWidget()
    lay = QHBoxLayout(spacer)
    lay.setContentsMargins(0, 0, 0, 0)
    spacer.setSizePolicy(spacer.sizePolicy().Expanding, spacer.sizePolicy().Preferred)
    toolbar.addWidget(spacer)

    toolbar.addAction(back_action)

    return (
        toolbar,
        org_action,
        contagents_action,
        archive_action,
        documents_action,
        settings_action,
        refresh_action,
        back_action,
    )
