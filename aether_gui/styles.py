"""
Aether GUI — Theme & Stylesheet
"""

COLORS = {
    "bg":           "#0a0a12",
    "bg2":          "#0e0e1a",
    "surface":      "#141420",
    "surface2":     "#1c1c2e",
    "surface3":     "#24243a",
    "accent":       "#6c63ff",
    "accent2":      "#a78bfa",
    "accent_glow":  "#6c63ff40",
    "text":         "#e4e4f0",
    "text2":        "#9494b8",
    "text3":        "#5e5e80",
    "danger":       "#ff5c7c",
    "success":      "#4ade80",
    "warning":      "#fbbf24",
    "border":       "#2a2a42",
    "border2":      "#3a3a5c",
    "white":        "#ffffff",
}

QSS = """
/* ── Global ── */
* {{
    font-family: 'Segoe UI', 'Inter', 'SF Pro Display', sans-serif;
}}
QMainWindow, QWidget {{
    background-color: {bg};
    color: {text};
    font-size: 14px;
}}

/* ── Labels ── */
QLabel {{
    background: transparent;
    border: none;
}}
QLabel#brand {{
    font-size: 28px;
    font-weight: 800;
    color: {accent};
    letter-spacing: 2px;
}}
QLabel#pageTitle {{
    font-size: 22px;
    font-weight: 700;
    color: {text};
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {text3};
}}
QLabel#statusDot {{
    font-size: 12px;
}}
QLabel#statValue {{
    font-size: 26px;
    font-weight: 700;
    color: {text};
}}
QLabel#statLabel {{
    font-size: 11px;
    color: {text3};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {surface2};
    color: {text};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {surface3};
    border-color: {border2};
}}
QPushButton:pressed {{
    background-color: {border};
}}
QPushButton:disabled {{
    background-color: {surface};
    color: {text3};
    border-color: {surface2};
}}
QPushButton#accentBtn {{
    background-color: {accent};
    color: {white};
    border: none;
    font-weight: 700;
    border-radius: 10px;
}}
QPushButton#accentBtn:hover {{
    background-color: {accent2};
}}
QPushButton#accentBtn:pressed {{
    background-color: #5a52e0;
}}
QPushButton#dangerBtn {{
    background-color: {danger};
    color: {white};
    border: none;
    font-weight: 700;
}}
QPushButton#dangerBtn:hover {{
    background-color: #ff7a94;
}}
QPushButton#navBtn {{
    background: transparent;
    color: {text3};
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}}
QPushButton#navBtn:hover {{
    background-color: {surface2};
    color: {text};
}}
QPushButton#navBtn:checked {{
    background-color: {surface2};
    color: {accent};
    border-left: 3px solid {accent};
}}

/* ── ComboBox ── */
QComboBox {{
    background-color: {surface2};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    min-height: 20px;
}}
QComboBox:hover {{
    border-color: {accent};
}}
QComboBox:focus {{
    border-color: {accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 32px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {text2};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {surface2};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    selection-background-color: {accent};
    selection-color: {white};
    padding: 4px;
    outline: none;
}}

/* ── Line Edit ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: {accent};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {accent};
}}

/* ── CheckBox ── */
QCheckBox {{
    spacing: 10px;
    font-size: 14px;
    color: {text};
}}
QCheckBox::indicator {{
    width: 22px;
    height: 22px;
    border-radius: 6px;
    border: 2px solid {border2};
    background: {surface};
}}
QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

/* ── Scrollbar ── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {surface3};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {text3};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* ── Tab Widget ── */
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 10px;
    background: {surface};
}}
QTabBar::tab {{
    background: {surface};
    color: {text3};
    padding: 10px 20px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 2px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background: {surface2};
    color: {accent};
    border-bottom: 2px solid {accent};
}}
QTabBar::tab:hover {{
    color: {text};
}}

/* ── ToolTip ── */
QToolTip {{
    background-color: {surface3};
    color: {text};
    border: 1px solid {border2};
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 12px;
}}

/* ── Frame cards ── */
QFrame#card {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 20px;
}}
QFrame#card:hover {{
    border-color: {accent};
}}
QFrame#sidebar {{
    background-color: {bg2};
    border-right: 1px solid {border};
}}
""".format(**COLORS)
