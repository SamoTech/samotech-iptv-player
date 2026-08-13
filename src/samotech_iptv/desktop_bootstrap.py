"""Desktop Qt composition factory for the libVLC player shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference
from samotech_iptv.infrastructure.player.composition import build_player
from samotech_iptv.presentation.theme import apply_theme
from samotech_iptv.presentation.views.main_window import MainWindow

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
    from samotech_iptv.application.use_cases.configure_xmltv_binding import ConfigureXMLTVBinding
    from samotech_iptv.application.use_cases.list_providers import ListProviders
    from samotech_iptv.application.use_cases.load_categories import LoadCategories
    from samotech_iptv.application.use_cases.load_registered_epg import LoadRegisteredEPG
    from samotech_iptv.application.use_cases.load_theme_preference import LoadThemePreference
    from samotech_iptv.application.use_cases.play_registered_channel import (
        PlayRegisteredChannel,
    )
    from samotech_iptv.application.use_cases.playback_controls import (
        PausePlayback,
        ResumePlayback,
        StopPlayback,
    )
    from samotech_iptv.application.use_cases.provider_lifecycle import (
        RemoveProvider,
        UpdateProvider,
    )
    from samotech_iptv.application.use_cases.refresh_xmltv_guide import RefreshXMLTVGuide
    from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider
    from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider
    from samotech_iptv.application.use_cases.register_xtream_provider import (
        RegisterXtreamProvider,
    )
    from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
    from samotech_iptv.application.use_cases.save_theme_preference import SaveThemePreference
    from samotech_iptv.application.use_cases.search_registered_channels import (
        SearchRegisteredChannels,
    )
    from samotech_iptv.application.use_cases.start_recording import StartRecording
    from samotech_iptv.application.use_cases.stop_recording import StopRecording

__all__ = ["DesktopApplication", "build_desktop_application"]


@dataclass(frozen=True)
class DesktopApplication:
    """Composed Qt application, its top-level window, and optional cleanup callback."""

    application: QApplication
    main_window: MainWindow
    close: Callable[[], Awaitable[None]] | None = None


def build_desktop_application(
    register_xtream_provider: RegisterXtreamProvider,
    register_m3u_provider: RegisterM3UProvider,
    register_mag_provider: RegisterMAGProvider,
    list_providers: ListProviders,
    load_categories: LoadCategories,
    update_provider: UpdateProvider,
    remove_provider: RemoveProvider,
    browse_channels: BrowseChannels,
    play_registered_channel: PlayRegisteredChannel,
    search_registered_channels: SearchRegisteredChannels,
    save_favorite: SaveFavorite,
    load_registered_epg: LoadRegisteredEPG,
    configure_xmltv_binding: ConfigureXMLTVBinding,
    refresh_xmltv_guide: RefreshXMLTVGuide,
    load_theme_preference: LoadThemePreference,
    save_theme_preference: SaveThemePreference,
    start_recording: StartRecording,
    stop_recording: StopRecording,
    pause_playback: PausePlayback,
    resume_playback: ResumePlayback,
    stop_playback: StopPlayback,
    initial_theme: ThemePreference = ThemePreference.SYSTEM,
    argv: Sequence[str] | None = None,
    player: PlayerPort | None = None,
) -> DesktopApplication:
    """Compose the Qt shell around externally configured registered-provider logic."""
    application = QApplication.instance() or QApplication(list(argv or []))
    apply_theme(application, initial_theme)
    desktop_player = player or build_player()
    main_window = MainWindow(
        desktop_player,
        register_xtream_provider,
        register_m3u_provider,
        register_mag_provider,
        list_providers,
        load_categories,
        update_provider,
        remove_provider,
        browse_channels,
        play_registered_channel,
        search_registered_channels,
        save_favorite,
        load_registered_epg,
        configure_xmltv_binding,
        refresh_xmltv_guide,
        load_theme_preference,
        save_theme_preference,
        start_recording,
        stop_recording,
        pause_playback,
        resume_playback,
        stop_playback,
    )
    return DesktopApplication(application=application, main_window=main_window)
