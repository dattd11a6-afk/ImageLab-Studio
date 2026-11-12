"""
ImageLab Studio - Dark Creative Studio Design System
Professional QSS styling matching Adobe Lightroom / Photoshop aesthetics.
"""

THEME_COLORS = {
    "background": "#121418",
    "sidebar": "#191D24",
    "panel": "#20252D",
    "panel_hover": "#262C36",
    "border": "#303743",
    "border_focus": "#60A5FA",
    "primary": "#60A5FA",
    "primary_hover": "#93C5FD",
    "primary_pressed": "#3B82F6",
    "accent": "#8B5CF6",
    "accent_hover": "#A78BFA",
    "success": "#34D399",
    "warning": "#FBBF24",
    "danger": "#F87171",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "histogram_orig": "#94A3B8",
    "histogram_adj": "#60A5FA",
}

DARK_STYLESHEET = f"""
/* ==========================================================
   ImageLab Studio - Global Dark Creative Theme
   ========================================================== */

* {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: {THEME_COLORS['text_primary']};
    outline: none;
}}

QMainWindow {{
    background-color: {THEME_COLORS['background']};
}}

QWidget {{
    background-color: transparent;
}}

/* Top Menu Bar */
QMenuBar {{
    background-color: {THEME_COLORS['sidebar']};
    border-bottom: 1px solid {THEME_COLORS['border']};
    padding: 2px 6px;
    font-size: 13px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    color: {THEME_COLORS['text_primary']};
}}

QMenuBar::item:selected {{
    background-color: {THEME_COLORS['panel']};
    color: {THEME_COLORS['primary']};
}}

QMenu {{
    background-color: {THEME_COLORS['panel']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 6px;
    padding: 4px 0px;
}}

QMenu::item {{
    padding: 6px 28px 6px 20px;
    border-radius: 4px;
    margin: 2px 4px;
}}

QMenu::item:selected {{
    background-color: {THEME_COLORS['panel_hover']};
    color: {THEME_COLORS['primary']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {THEME_COLORS['border']};
    margin: 4px 8px;
}}

/* Toolbars */
QToolBar {{
    background-color: {THEME_COLORS['sidebar']};
    border-bottom: 1px solid {THEME_COLORS['border']};
    spacing: 6px;
    padding: 4px 8px;
}}

QToolButton {{
    background-color: transparent;
    color: {THEME_COLORS['text_primary']};
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 5px 10px;
    font-weight: 500;
}}

QToolButton:hover {{
    background-color: {THEME_COLORS['panel']};
    border: 1px solid {THEME_COLORS['border']};
}}

QToolButton:pressed {{
    background-color: {THEME_COLORS['border']};
}}

QToolButton:checked {{
    background-color: #1e3a5f;
    border: 1px solid {THEME_COLORS['primary']};
    color: {THEME_COLORS['primary']};
}}

/* Panels and Containers */
QFrame#panelFrame {{
    background-color: {THEME_COLORS['panel']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 8px;
}}

QFrame#sidebarFrame {{
    background-color: {THEME_COLORS['sidebar']};
    border-left: 1px solid {THEME_COLORS['border']};
}}

/* Push Buttons */
QPushButton {{
    background-color: {THEME_COLORS['panel']};
    color: {THEME_COLORS['text_primary']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {THEME_COLORS['panel_hover']};
    border-color: {THEME_COLORS['border_focus']};
}}

QPushButton:pressed {{
    background-color: #1a222d;
    border-color: {THEME_COLORS['primary_pressed']};
}}

QPushButton:disabled {{
    background-color: #16191f;
    color: {THEME_COLORS['text_muted']};
    border-color: #242a34;
}}

/* Primary Accent Button */
QPushButton#primaryButton {{
    background-color: {THEME_COLORS['primary']};
    color: #0b111a;
    font-weight: 600;
    border: none;
}}

QPushButton#primaryButton:hover {{
    background-color: {THEME_COLORS['primary_hover']};
}}

QPushButton#primaryButton:pressed {{
    background-color: {THEME_COLORS['primary_pressed']};
}}

/* Accent Purple Button */
QPushButton#accentButton {{
    background-color: {THEME_COLORS['accent']};
    color: #ffffff;
    font-weight: 600;
    border: none;
}}

QPushButton#accentButton:hover {{
    background-color: {THEME_COLORS['accent_hover']};
}}

/* Small Reset Button */
QPushButton#resetBtn {{
    background-color: transparent;
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    color: {THEME_COLORS['text_secondary']};
}}

QPushButton#resetBtn:hover {{
    background-color: {THEME_COLORS['panel_hover']};
    color: {THEME_COLORS['primary']};
    border-color: {THEME_COLORS['primary']};
}}

/* Parameter Individual Reset Button (28x28px) */
QPushButton#paramResetBtn {{
    background-color: transparent;
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
    color: {THEME_COLORS['text_secondary']};
    padding: 0px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}}

QPushButton#paramResetBtn:hover {{
    background-color: {THEME_COLORS['panel_hover']};
    color: {THEME_COLORS['primary']};
    border-color: {THEME_COLORS['primary']};
}}

QPushButton#paramResetBtn:pressed {{
    background-color: #1a222d;
}}

/* Analysis Panel Expand/Restore ToolButton (28x28px) */
QToolButton#analysisExpandBtn {{
    background-color: {THEME_COLORS['panel']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 4px;
    padding: 0px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}}

QToolButton#analysisExpandBtn:hover {{
    background-color: {THEME_COLORS['panel_hover']};
    border-color: {THEME_COLORS['primary']};
}}

QToolButton#analysisExpandBtn:pressed {{
    background-color: #1a222d;
}}

/* SpinBoxes */
QSpinBox, QDoubleSpinBox {{
    background-color: {THEME_COLORS['sidebar']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 5px;
    padding: 3px 6px;
    color: {THEME_COLORS['text_primary']};
    font-weight: 500;
    min-width: 65px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {THEME_COLORS['primary']};
    background-color: #1a202c;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: transparent;
    width: 14px;
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 4px;
    background: #2a313d;
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {THEME_COLORS['primary']};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: #ffffff;
    border: 2px solid {THEME_COLORS['primary']};
    width: 14px;
    height: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {THEME_COLORS['primary_hover']};
    border-color: #ffffff;
}}

QSlider::handle:horizontal:disabled {{
    background: {THEME_COLORS['text_muted']};
    border-color: #3b4352;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {THEME_COLORS['border']};
    background-color: {THEME_COLORS['panel']};
    border-radius: 6px;
    top: -1px;
}}

QTabBar::tab {{
    background: {THEME_COLORS['sidebar']};
    color: {THEME_COLORS['text_secondary']};
    border: 1px solid {THEME_COLORS['border']};
    border-bottom: none;
    padding: 7px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background: {THEME_COLORS['panel']};
    color: {THEME_COLORS['primary']};
    border-bottom: 2px solid {THEME_COLORS['primary']};
}}

QTabBar::tab:hover:!selected {{
    background: {THEME_COLORS['panel_hover']};
    color: {THEME_COLORS['text_primary']};
}}

/* Scroll Areas & Scroll Bars */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: {THEME_COLORS['sidebar']};
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: #374151;
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #4b5563;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {THEME_COLORS['sidebar']};
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: #374151;
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: #4b5563;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
    width: 0px;
}}

/* Tables */
QTableWidget {{
    background-color: {THEME_COLORS['sidebar']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 6px;
    gridline-color: #242c38;
    color: {THEME_COLORS['text_primary']};
    selection-background-color: #1e3a5f;
    selection-color: {THEME_COLORS['text_primary']};
}}

QTableWidget::item {{
    padding: 6px 10px;
}}

QHeaderView::section {{
    background-color: {THEME_COLORS['panel']};
    color: {THEME_COLORS['text_secondary']};
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {THEME_COLORS['border']};
    font-weight: 600;
    font-size: 12px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {THEME_COLORS['sidebar']};
    border-top: 1px solid {THEME_COLORS['border']};
    color: {THEME_COLORS['text_secondary']};
    font-size: 12px;
    padding: 2px 8px;
}}

QStatusBar QLabel {{
    color: {THEME_COLORS['text_secondary']};
    font-size: 12px;
}}

/* Tooltips */
QToolTip {{
    background-color: #1A1F29;
    color: #F8FAFC;
    border: 1px solid #60A5FA;
    padding: 6px 10px;
    border-radius: 5px;
    font-size: 12px;
}}

/* Splitters */
QSplitter::handle {{
    background-color: {THEME_COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* Labels and GroupBoxes */
QGroupBox {{
    font-weight: 600;
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    background-color: {THEME_COLORS['panel']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {THEME_COLORS['primary']};
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 0.5px;
}}

QComboBox {{
    background-color: {THEME_COLORS['sidebar']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 5px;
    padding: 4px 8px;
    color: {THEME_COLORS['text_primary']};
}}

QComboBox:hover {{
    border-color: {THEME_COLORS['border_focus']};
}}

QComboBox QAbstractItemView {{
    background-color: {THEME_COLORS['panel']};
    border: 1px solid {THEME_COLORS['border']};
    selection-background-color: #1e3a5f;
    color: {THEME_COLORS['text_primary']};
}}
"""

