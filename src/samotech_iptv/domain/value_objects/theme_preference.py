"""Canonical user-selectable desktop theme preferences."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["ThemePreference"]


class ThemePreference(StrEnum):
    """Supported user theme preferences independent of the Qt implementation."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"
