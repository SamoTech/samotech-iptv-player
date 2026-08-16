"""Apply deterministic Qt application styles for supported theme preferences."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference
from samotech_iptv.presentation.theme.tokens import COLORS, RADII, SPACING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

__all__ = ["DARK_STYLESHEET", "LIGHT_STYLESHEET", "apply_theme"]

DARK_STYLESHEET = f"""
QWidget {{
    background-color: {COLORS.background};
    color: {COLORS.text};
    font-size: 13px;
}}
QToolTip {{
    background-color: {COLORS.surface_elevated};
    color: {COLORS.text};
    border: 1px solid {COLORS.border_strong};
    padding: {SPACING.sm}px;
}}
QPushButton {{
    background-color: {COLORS.surface_elevated};
    color: {COLORS.text};
    border: 1px solid {COLORS.border};
    border-radius: {RADII.sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
}}
QPushButton:hover, QPushButton:focus {{
    background-color: {COLORS.primary_muted};
    border-color: {COLORS.primary_hover};
}}
QPushButton:disabled {{
    color: {COLORS.text_disabled};
    border-color: {COLORS.surface_elevated};
}}
QLineEdit, QComboBox {{
    background-color: {COLORS.surface};
    color: {COLORS.text};
    border: 1px solid {COLORS.border};
    border-radius: {RADII.sm}px;
    padding: {SPACING.sm}px {SPACING.md}px;
    selection-background-color: {COLORS.primary};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {COLORS.primary_hover};
}}
QScrollBar:vertical {{
    background: {COLORS.surface_muted};
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS.border_strong};
    border-radius: 5px;
    min-height: 30px;
}}
"""

LIGHT_STYLESHEET = """
QWidget {
    background-color: #f4f6fa;
    color: #17202b;
    font-size: 13px;
}
QPushButton {
    background-color: #ffffff;
    color: #17202b;
    border: 1px solid #c8d1de;
    border-radius: 6px;
    padding: 8px 12px;
}
QPushButton:hover, QPushButton:focus {
    background-color: #e7f1ff;
    border-color: #2f8cff;
}
QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #17202b;
    border: 1px solid #c8d1de;
    border-radius: 6px;
    padding: 8px 12px;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #2f8cff;
}
"""


def apply_theme(application: QApplication, preference: ThemePreference) -> None:
    """Apply one safe application-wide theme without reading provider or user data."""
    stylesheet = {
        ThemePreference.SYSTEM: DARK_STYLESHEET,
        ThemePreference.LIGHT: LIGHT_STYLESHEET,
        ThemePreference.DARK: DARK_STYLESHEET,
    }[preference]
    application.setStyleSheet(stylesheet)
