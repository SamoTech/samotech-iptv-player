from __future__ import annotations

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference
from samotech_iptv.presentation.theme.theme_engine import (
    DARK_STYLESHEET,
    LIGHT_STYLESHEET,
    apply_theme,
)


class FakeApplication:
    """Minimal QApplication double retaining the applied application stylesheet."""

    def __init__(self) -> None:
        self.stylesheets: list[str] = []

    def setStyleSheet(self, stylesheet: str) -> None:  # noqa: N802
        self.stylesheets.append(stylesheet)


def test_theme_engine_applies_supported_preferences() -> None:
    application = FakeApplication()

    apply_theme(application, ThemePreference.SYSTEM)  # type: ignore[arg-type]
    apply_theme(application, ThemePreference.LIGHT)  # type: ignore[arg-type]
    apply_theme(application, ThemePreference.DARK)  # type: ignore[arg-type]

    assert application.stylesheets == [DARK_STYLESHEET, LIGHT_STYLESHEET, DARK_STYLESHEET]
