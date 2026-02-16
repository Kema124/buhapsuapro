from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer


def _candidates() -> list[str]:
    here = os.path.dirname(__file__)      # ui/
    proj = os.path.dirname(here)          # project root approx
    return [
        os.path.join(here, "assets"),
        os.path.join(proj, "assets"),
        os.path.join(os.getcwd(), "assets"),
    ]


def asset_path(name: str) -> str:
    for base in _candidates():
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return os.path.join(_candidates()[0], name)


def icon_path(name: str) -> str:
    for base in _candidates():
        p = os.path.join(base, "icons", name)
        if os.path.exists(p):
            return p
    return os.path.join(_candidates()[0], "icons", name)


def load_pixmap(name: str) -> QPixmap:
    return QPixmap(asset_path(name))


@lru_cache(maxsize=256)
def _render_svg_icon(path: str, color_hex: str) -> QIcon:
    """
    Рендерим SVG в пиксмапы разных размеров и красим stroke/fill.
    В SVG должны быть stroke="currentColor" (и/или fill="currentColor").
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            svg_txt = f.read()
    except Exception:
        return QIcon()

    svg_txt = svg_txt.replace("currentColor", color_hex)
    data = QByteArray(svg_txt.encode("utf-8"))

    renderer = QSvgRenderer(data)
    if not renderer.isValid():
        return QIcon()

    icon = QIcon()
    for size in (16, 18, 20, 22, 24):
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()

        icon.addPixmap(pm)
    return icon


def load_icon(name: str, *, color: Optional[str] = None) -> QIcon:
    """
    Если svg — можем задать цвет.
    """
    if name.lower().endswith(".svg"):
        p = icon_path(name)
        if os.path.exists(p):
            if color is None:
                # по умолчанию пусть будет “тёмный” (для светлой темы)
                color = "#22324a"
            return _render_svg_icon(p, color)
        return QIcon.fromTheme(name)

    p = asset_path(name)
    if os.path.exists(p):
        return QIcon(p)

    return QIcon.fromTheme(name)
