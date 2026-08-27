"""Shared styling helpers for compact, accessible desktop dialogs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.presentation.theme.tokens import COLORS, RADII

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


__all__ = ["apply_form_dialog_style"]


_FORM_DIALOG_STYLE = f"""
QDialog {{
    background: {COLORS.background};
    color: {COLORS.text};
}}
QLabel {{
    color: {COLORS.text};
}}
QLabel#formHelp {{
    color: {COLORS.text_muted};
    padding: 4px 0 8px 0;
}}
QLabel#formStatus {{
    color: {COLORS.text_muted};
    padding-top: 8px;
}}
QLineEdit, QComboBox {{
    background: {COLORS.surface};
    border: 1px solid {COLORS.border};
    border-radius: {RADII.sm}px;
    padding: 8px 10px;
    color: {COLORS.text};
    selection-background-color: {COLORS.primary};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {COLORS.primary_hover};
}}
QPushButton {{
    background: {COLORS.surface_elevated};
    border: 1px solid {COLORS.border_strong};
    border-radius: {RADII.sm}px;
    padding: 8px 12px;
    color: {COLORS.text};
    min-height: 18px;
}}
QPushButton:hover, QPushButton:focus {{
    background: {COLORS.primary_muted};
    border-color: {COLORS.primary_hover};
}}
QPushButton#primary {{
    background: {COLORS.primary};
    border-color: {COLORS.primary_hover};
    font-weight: 700;
}}
QPushButton#primary:hover, QPushButton#primary:focus {{
    background: {COLORS.primary_hover};
}}
QPushButton#destructive {{
    color: {COLORS.danger};
    border-color: {COLORS.danger};
}}
QPushButton#destructive:hover, QPushButton#destructive:focus {{
    background: rgba(244, 126, 136, 32);
}}
QPushButton:disabled {{
    color: {COLORS.text_disabled};
    background: {COLORS.surface_muted};
    border-color: {COLORS.border};
}}
QCheckBox {{
    color: {COLORS.text_muted};
    spacing: 8px;
}}
QCheckBox:focus {{
    color: {COLORS.text};
}}
"""


def apply_form_dialog_style(dialog: QWidget) -> None:
    """Apply the shared dark form style to a dialog or compact form widget."""
    dialog.setStyleSheet(_FORM_DIALOG_STYLE)
