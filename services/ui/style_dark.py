from __future__ import annotations

DARK_QSS = """
QMainWindow { background: #1e2430; }
QWidget { background: #1e2430; color: #e8eef7; }

/* Toolbar always dark */
QToolBar {
    background: #0f2f5c;
    border: none;
    spacing: 6px;
    padding: 6px;
}
QToolBar * { color: #e8eef7; }

QToolButton {
    background: transparent;
    border: none;
    padding: 6px 10px;
    border-radius: 8px;
}
QToolButton:hover { background: rgba(255,255,255,0.12); }
QToolButton:pressed { background: rgba(255,255,255,0.18); }

/* Sidebar */
#Sidebar {
    background: #141a24;
    border-right: 1px solid #2a3142;
}
#SidebarButton {
    text-align: left;
    padding: 9px 10px;
    border-radius: 10px;
    border: none;
    background: transparent;
    color: #e8eef7;
}
#SidebarButton:hover { background: #222a3a; }
#SidebarButton:pressed { background: #2a3142; }
#SidebarButton[active="true"] {
    background: #2a3142;
    font-weight: 800;
}

/* Tabs */
QTabWidget::pane { border: none; }
QTabBar::tab {
    background: #2a3142;
    padding: 9px 14px;
    padding-right: 30px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background: #364058;
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
    background: rgba(255,255,255,0.10);
    border-radius: 6px;
}

/* Inputs */
QLineEdit, QComboBox, QDateEdit, QTextEdit {
    background: #1f2635;
    border: 1px solid #364058;
    border-radius: 8px;
    padding: 7px 10px;
    color: #e8eef7;
}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QTextEdit:hover {
    border: 1px solid #4a556f;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #9bb7ff;
}

/* Tables */
QAbstractItemView {
    background: #2a3142;
    border: 1px solid #364058;
    color: #e8eef7;
}
QHeaderView::section {
    background: #1f2635;
    border: none;
    padding: 6px;
    font-weight: 800;
    color: #e8eef7;
}
QAbstractItemView::item:hover { background: #2f3a52; }
QAbstractItemView::item:selected { background: #2fbf6a; color: #0b1410; }

/* Buttons */
QPushButton {
    background: #1b4f9c;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 7px 12px;
    font-weight: 800;
}
QPushButton:hover { background: #2fbf6a; }
QPushButton:pressed { background: #168a4a; }

/* StatusBar */
QStatusBar { background: #0f2f5c; color: #e8eef7; font-weight: 800; }

/* ===== UT Filter Panel ===== */
#UTFilterPanel { border: 1px solid #2a3646; border-radius: 10px; }
#UTFilterTitle { font-size: 14px; font-weight: 700; color: #e8eef7; }
#UTFilterBody {
    background: #121a24;
    border-top: 1px solid #2a3646;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
}
#UTFilterTree {
    background: #0f151f;
    border: 1px solid #2a3646;
    border-radius: 8px;
    color: #e8eef7;
}
#UTFilterTree::item:hover { background: #1a2736; }
#UTFilterAdd, #UTFilterAddGroup { padding: 6px 10px; border-radius: 8px; }
#UTFilterApply { padding: 7px 14px; border-radius: 8px; font-weight: 700; }
#UTFilterReset { padding: 7px 14px; border-radius: 8px; }
#UTFilterRemove { border-radius: 6px; padding: 2px 0; }
"""
