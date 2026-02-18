from __future__ import annotations

LIGHT_QSS = """
QMainWindow { background: #f4f6f9; }
QWidget { background: #f4f6f9; color: #1f2d3d; }

/* Toolbar always dark */
QToolBar {
    background: #1f3c73;
    border: none;
    spacing: 6px;
    padding: 6px;
}
QToolBar * { color: white; }

QToolButton {
    background: transparent;
    border: none;
    padding: 6px 10px;
    border-radius: 8px;
}
QToolButton:hover { background: rgba(255,255,255,0.14); }
QToolButton:pressed { background: rgba(255,255,255,0.22); }

/* Sidebar */
#Sidebar {
    background: #eef3fb;
    border-right: 1px solid #dbe2ef;
}
#SidebarButton {
    text-align: left;
    padding: 9px 10px;
    border-radius: 10px;
    border: none;
    background: transparent;
    color: #22324a;
}
#SidebarButton:hover { background: #dfe9fb; }
#SidebarButton:pressed { background: #cfe0ff; }
#SidebarButton[active="true"] {
    background: #cfe0ff;
    font-weight: 800;
}

/* Tabs */
QTabWidget::pane { border: none; }
QTabBar::tab {
    background: #e8eef7;
    padding: 9px 14px;
    padding-right: 30px; /* место под крестик внутри */
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background: #ffffff;
    font-weight: 800;
}
QTabBar::close-button {
    image: url(%CLOSE_SVG%);
    subcontrol-origin: padding;
    subcontrol-position: right center;
    margin-right: 8px;
    width: 14px;
    height: 14px;
}
QTabBar::close-button:hover {
    background: rgba(31,60,115,0.12);
    border-radius: 6px;
}

/* Inputs */
QLineEdit, QComboBox, QDateEdit, QTextEdit {
    background: #ffffff;
    border: 1px solid #dbe2ef;
    border-radius: 8px;
    padding: 7px 10px;
    color: #1f2d3d;
}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QTextEdit:hover {
    border: 1px solid #b9c7e3;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #2c5fb8;
}

/* Tables */
QAbstractItemView {
    background: #ffffff;
    border: 1px solid #dbe2ef;
}
QHeaderView::section {
    background: #f1f5fb;
    border: none;
    padding: 6px;
    font-weight: 800;
}
QAbstractItemView::item:hover { background: #e7f0ff; }
QAbstractItemView::item:selected { background: #cde1ff; color: #102033; }

/* Buttons */
QPushButton {
    background: #1f3c73;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 7px 12px;
    font-weight: 800;
}
QPushButton:hover { background: #2c5fb8; }
QPushButton:pressed { background: #17305c; }

/* StatusBar */
QStatusBar { background: #1f3c73; color: white; font-weight: 800; }

/* ===== UT Filter Panel ===== */
#UTFilterPanel { border: 1px solid #d6dde7; border-radius: 10px; }
#UTFilterTitle { font-size: 14px; font-weight: 700; color: #1b2a40; }
#UTFilterBody {
    background: #f7f9fc;
    border-top: 1px solid #d6dde7;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
}
#UTFilterTree {
    background: white;
    border: 1px solid #d6dde7;
    border-radius: 8px;
}
#UTFilterTree::item:hover { background: #eaf2ff; }
#UTFilterAdd, #UTFilterAddGroup { padding: 6px 10px; border-radius: 8px; }
#UTFilterApply { padding: 7px 14px; border-radius: 8px; font-weight: 700; }
#UTFilterReset { padding: 7px 14px; border-radius: 8px; }
#UTFilterRemove { border-radius: 6px; padding: 2px 0; }
"""
