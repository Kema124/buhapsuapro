from __future__ import annotations

from PySide6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QAction
from PySide6.QtCore import QSize

from ui.assets import load_icon


def create_toolbar(parent):
    toolbar = QToolBar()
    toolbar.setMovable(False)
    toolbar.setFloatable(False)

    # фиксированный размер иконок (одинаково на всех темах)
    toolbar.setIconSize(QSize(20, 20))

    # toolbar всегда тёмный -> иконки делаем светлыми
    color = "#ffffff"

    org_action = QAction(load_icon("organization.svg", color=color), "Организация", parent)
    contagents_action = QAction(load_icon("users.svg", color=color), "Контрагенты", parent)
    archive_action = QAction(load_icon("archive.svg", color=color), "Архив", parent)
    documents_action = QAction(load_icon("documents.svg", color=color), "Документы", parent)
    settings_action = QAction(load_icon("settings.svg", color=color), "Настройки", parent)
    refresh_action = QAction(load_icon("refresh.svg", color=color), "Обновить", parent)
    back_action = QAction(load_icon("back.svg", color=color), "Базы", parent)

    toolbar.addAction(documents_action)
    toolbar.addAction(contagents_action)
    toolbar.addAction(archive_action)
    toolbar.addAction(org_action)
    toolbar.addAction(refresh_action)
    toolbar.addSeparator()
    toolbar.addAction(settings_action)

    # растяжка вправо
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    toolbar.addWidget(spacer)

    # кнопка "Базы" справа
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
