"""Shared visual tokens for the desktop IPTV presentation layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class _Colors:
    background: str = "#080b10"
    surface: str = "#111722"
    surface_elevated: str = "#172131"
    surface_muted: str = "#0d131c"
    border: str = "#263449"
    border_strong: str = "#35506f"
    primary: str = "#2f8cff"
    primary_hover: str = "#4ca3ff"
    primary_muted: str = "#173d67"
    text: str = "#f3f7fc"
    text_muted: str = "#9aa9bd"
    text_disabled: str = "#5e6b7c"
    success: str = "#57d19a"
    warning: str = "#f0bd67"
    danger: str = "#f47e88"
    video: str = "#020408"


@dataclass(frozen=True)
class _Spacing:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True)
class _Radii:
    sm: int = 6
    md: int = 10
    lg: int = 14


COLORS = _Colors()
SPACING = _Spacing()
RADII = _Radii()

__all__ = ["COLORS", "RADII", "SPACING"]
