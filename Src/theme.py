"""Fable's violet/plum/cream application palette; grading colors remain semantic."""

BACKGROUND = "#171327"
SURFACE = "#241d38"
BORDER = "#4b3c64"
ACCENT = "#b79aff"
CREAM = "#fff0cf"
MUTED = "#baaacf"

# Explanation panels are informational, separate from green/red answer grading.
EXPLANATIONS = {
    True: ("#cfe8ff", "#20364f", "#83b8e8", "Correct"),
    False: ("#ffe0b2", "#49301e", "#e5aa64", "Incorrect"),
}


def explanation_style(correct):
    text, background, border, _ = EXPLANATIONS[bool(correct)]
    return (
        f"QLabel {{background:{background};color:{text};border:1px solid {border};"
        "border-radius:10px;padding:16px;}"
    )


STYLE = """
QWidget {background:#171327;color:#f3eaf9;font-family:"Segoe UI";font-size:11pt;}
QMainWindow {background:#110e1d;}
QLabel#title {font-size:23pt;font-weight:700;color:#fff0cf;}
QLabel#brand {font-size:26pt;font-weight:750;color:#fff0cf;}
QLabel#brandSub {font-size:10pt;color:#c8b7e5;}
QLabel#muted {color:#baaacf;font-size:10pt;}
QLabel#prompt {font-size:16pt;font-weight:600;line-height:150%;color:#fff5e0;}
QLabel#banner {padding:16px;background:#34244d;border:1px solid #5c437c;border-radius:10px;color:#eadbff;}
QFrame#examBanner {background:#34244d;border:1px solid #5c437c;border-radius:10px;}
QLabel#examBannerText,QLabel#examTime {background:transparent;color:#eadbff;}
QLabel#examTime {font-family:Consolas,"DejaVu Sans Mono",monospace;font-weight:600;}
QLabel#xp {background:transparent;border:0;padding:0;color:#baaacf;font-size:11pt;}
QFrame#card {background:#241d38;border:1px solid #4b3c64;border-radius:14px;}
QPushButton {background:#302442;border:1px solid #5a4576;border-radius:8px;padding:9px 15px;font-weight:600;}
QPushButton:hover {background:#49335f;border-color:#c6a8ff;}
QPushButton:focus {border-color:#c6a8ff;}
QPushButton:disabled {color:#847292;background:#251d32;}
QPushButton#primary {background:#b79aff;color:#211333;border-color:#b79aff;}
QPushButton#primary:hover {background:#c9b2ff;}
QPushButton#primary:disabled {background:#352546;color:#9785a6;border-color:#4b375f;}
QPushButton#syncNarration {background:#f3ce8c;color:#241733;border-color:#f3ce8c;font-size:12pt;font-weight:700;}
QPushButton#syncNarration:hover {background:#ffe0a6;border-color:#ffe0a6;}
QPushButton#syncNarration:focus {border-color:#fff0cf;}
QPushButton#danger {color:#ffd0b0;border-color:#a16a5c;}
QListWidget,QTextBrowser,QTextEdit,QTableWidget {background:#211a31;border:1px solid #463556;border-radius:9px;padding:8px;}
QListWidget::item {padding:9px;border-radius:6px;}
QListWidget::item:selected {background:#493260;color:#fff0cf;}
QListWidget::item:hover {background:#332642;}
QRadioButton {background:#2b2240;border:1px solid #55416d;border-radius:9px;padding:13px;spacing:12px;}
QRadioButton:hover {border-color:#b79aff;}
QRadioButton:checked {background:#48315f;border:2px solid #c1a0ff;}
QRadioButton::indicator {width:17px;height:17px;}
QTabWidget::pane {border:0;}
QTabBar::tab {padding:13px 25px;background:#21182f;color:#c2b0d7;}
QTabBar::tab:selected {background:#38234e;color:#fff0cf;border-bottom:3px solid #b79aff;}
QComboBox,QSpinBox,QLineEdit {background:#2b213c;border:1px solid #59436f;border-radius:7px;padding:7px;}
QComboBox:focus,QSpinBox:focus,QLineEdit:focus {border:1px solid #c1a0ff;}
QComboBox QAbstractItemView {background:#2b213c;selection-background-color:#57396e;}
QProgressBar {background:#30223f;border:0;border-radius:5px;height:14px;text-align:center;color:#fff0cf;}
QProgressBar::chunk {background:#9b78e4;border-radius:5px;}
QHeaderView::section {background:#362746;color:#fff0cf;padding:8px;border:0;}
QSlider::groove:horizontal {height:6px;background:#59436c;}
QSlider::handle:horizontal {background:#d2b6ff;width:14px;margin:-5px 0;border-radius:6px;}
QTextEdit#transcript {font-size:14pt;padding:20px;selection-background-color:#66458b;}
QToolTip {background:#352443;color:#fff0cf;border:1px solid #b79aff;}
QScrollBar:vertical {background:#21192e;width:12px;margin:0;}
QScrollBar::handle:vertical {background:#664a80;min-height:24px;border-radius:6px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
QStatusBar {color:#baaacf;}
"""
