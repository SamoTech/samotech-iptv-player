"""Apply deterministic Qt application styles for the supported theme preferences."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

__all__ = ["apply_theme"]

_DARK_STYLESHEET = "QWidget { background-color: #202124; color: #f1f3f4; }"
_LIGHT_STYLESHEET = "QWidget { background-color: #ffffff; color: #202124; }"


def apply_theme(application: QApplication, preference: ThemePreference) -> None:
    """Apply one safe application-wide theme without reading provider or user data."""
    stylesheet = {
        ThemePreference.SYSTEM: "",
        ThemePreference.LIGHT: _LIGHT_STYLESHEET,
        ThemePreference.DARK: _DARK_STYLESHEET,
    }[preference]
    application.setStyleSheet(stylesheet)
