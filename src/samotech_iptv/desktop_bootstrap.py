"""PySide6 desktop composition for the VLC-only IPTV player."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

from samotech_iptv.infrastructure.player.composition import build_player
from samotech_iptv.presentation.views.main_window import MainWindow

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.use_cases.list_providers import ListProviders
    from samotech_iptv.application.use_cases.play_channel import PlayChannel
    from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider
    from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider
    from samotech_iptv.application.use_cases.register_xtream_provider import (
        RegisterXtreamProvider,
    )

__all__ = ["DesktopApplication", "build_desktop_application"]


@dataclass(frozen=True)
class DesktopApplication:
    """Composed Qt application and its top-level playback window."""

    application: QApplication
    main_window: MainWindow


def build_desktop_application(
    play_channel: PlayChannel,
    register_xtream_provider: RegisterXtreamProvider,
    register_m3u_provider: RegisterM3UProvider,
    register_mag_provider: RegisterMAGProvider,
    list_providers: ListProviders,
    argv: Sequence[str] | None = None,
) -> DesktopApplication:
    """Compose the Qt shell around externally configured provider playback logic."""
    application = QApplication.instance() or QApplication(list(argv or []))
    player = build_player()
    main_window = MainWindow(
        player,
        play_channel,
        register_xtream_provider,
        register_m3u_provider,
        register_mag_provider,
        list_providers,
    )
    return DesktopApplication(application=application, main_window=main_window)
