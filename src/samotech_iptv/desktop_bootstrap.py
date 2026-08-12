"""PySide6 desktop composition for the VLC-only IPTV player."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

from samotech_iptv.infrastructure.player.composition import build_player
from samotech_iptv.presentation.views.main_window import MainWindow

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.use_cases.play_channel import PlayChannel

__all__ = ["DesktopApplication", "build_desktop_application"]


@dataclass(frozen=True)
class DesktopApplication:
    """Composed Qt application and its top-level playback window."""

    application: QApplication
    main_window: MainWindow


def build_desktop_application(
    play_channel: PlayChannel, argv: Sequence[str] | None = None
) -> DesktopApplication:
    """Compose the Qt shell around externally configured provider playback logic."""
    application = QApplication.instance() or QApplication(list(argv or []))
    player = build_player()
    main_window = MainWindow(player, play_channel)
    return DesktopApplication(application=application, main_window=main_window)
