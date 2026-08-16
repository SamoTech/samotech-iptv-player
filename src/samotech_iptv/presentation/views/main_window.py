"""Main Qt application window hosting the native libVLC video surface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.tokens import COLORS, RADII
from samotech_iptv.presentation.widgets.vlc_video_surface import VlcVideoSurface

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.playback import PlaybackResult, PlaybackTarget
    from samotech_iptv.application.ports.artwork_port import ArtworkPort
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
    from samotech_iptv.application.use_cases.browse_content import BrowseContent
    from samotech_iptv.application.use_cases.clear_history import ClearHistory
    from samotech_iptv.application.use_cases.configure_xmltv_binding import ConfigureXMLTVBinding
    from samotech_iptv.application.use_cases.list_favorites import ListFavorites
    from samotech_iptv.application.use_cases.list_providers import ListProviders
    from samotech_iptv.application.use_cases.load_categories import LoadCategories
    from samotech_iptv.application.use_cases.load_history import LoadHistory
    from samotech_iptv.application.use_cases.load_movie_details import LoadMovieDetails
    from samotech_iptv.application.use_cases.load_provider_capabilities import (
        LoadProviderCapabilities,
    )
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
    from samotech_iptv.application.use_cases.remove_favorite import RemoveFavorite
    from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
    from samotech_iptv.application.use_cases.save_theme_preference import SaveThemePreference
    from samotech_iptv.application.use_cases.search_registered_channels import (
        SearchRegisteredChannels,
    )
    from samotech_iptv.application.use_cases.series_discovery import (
        LoadSeasonEpisodes,
        LoadSeriesSeasons,
    )
    from samotech_iptv.application.use_cases.start_recording import StartRecording
    from samotech_iptv.application.use_cases.stop_recording import StopRecording
    from samotech_iptv.presentation.dialogs.category_browser_dialog import (
        CategoryBrowserDialog,
    )
    from samotech_iptv.presentation.dialogs.channel_browser_dialog import (
        ChannelBrowserDialog,
    )
    from samotech_iptv.presentation.dialogs.epg_grid_dialog import EPGGridDialog
    from samotech_iptv.presentation.dialogs.favorites_library_dialog import (
        FavoritesLibraryDialog,
    )
    from samotech_iptv.presentation.dialogs.history_library_dialog import HistoryLibraryDialog
    from samotech_iptv.presentation.dialogs.m3u_provider_dialog import M3UProviderDialog
    from samotech_iptv.presentation.dialogs.mag_provider_dialog import MAGProviderDialog
    from samotech_iptv.presentation.dialogs.provider_list_dialog import ProviderListDialog
    from samotech_iptv.presentation.dialogs.theme_settings_dialog import ThemeSettingsDialog
    from samotech_iptv.presentation.dialogs.xmltv_guide_dialog import XMLTVGuideDialog
    from samotech_iptv.presentation.dialogs.xtream_provider_dialog import XtreamProviderDialog
    from samotech_iptv.presentation.player_shell import PlayerShell

__all__ = ["MainWindow"]


class MainWindow(QMainWindow):
    """Own the Qt video surface and delegate playback to application orchestration."""

    def __init__(
        self,
        player: PlayerPort,
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
        list_favorites: ListFavorites,
        remove_favorite: RemoveFavorite,
        load_history: LoadHistory,
        clear_history: ClearHistory,
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
        browse_content: BrowseContent | None = None,
        load_provider_capabilities: LoadProviderCapabilities | None = None,
        load_movie_details: LoadMovieDetails | None = None,
        load_series_seasons: LoadSeriesSeasons | None = None,
        load_season_episodes: LoadSeasonEpisodes | None = None,
        artwork_loader: ArtworkPort | None = None,
    ) -> None:
        super().__init__()
        self._register_xtream_provider = register_xtream_provider
        self._register_m3u_provider = register_m3u_provider
        self._register_mag_provider = register_mag_provider
        self._list_providers = list_providers
        self._load_categories = load_categories
        self._update_provider = update_provider
        self._remove_provider = remove_provider
        self._browse_channels = browse_channels
        self._play_registered_channel = play_registered_channel
        self._search_registered_channels = search_registered_channels
        self._save_favorite = save_favorite
        self._list_favorites = list_favorites
        self._remove_favorite = remove_favorite
        self._load_history = load_history
        self._clear_history = clear_history
        self._load_registered_epg = load_registered_epg
        self._configure_xmltv_binding = configure_xmltv_binding
        self._refresh_xmltv_guide = refresh_xmltv_guide
        self._load_theme_preference = load_theme_preference
        self._save_theme_preference = save_theme_preference
        self._start_recording = start_recording
        self._stop_recording = stop_recording
        self._pause_playback = pause_playback
        self._resume_playback = resume_playback
        self._stop_playback = stop_playback
        self._browse_content = browse_content
        self._load_provider_capabilities = load_provider_capabilities
        self._load_movie_details = load_movie_details
        self._load_series_seasons = load_series_seasons
        self._load_season_episodes = load_season_episodes
        self._artwork_loader = artwork_loader
        self.video_surface = VlcVideoSurface(player)
        self.setWindowTitle("SamoTech IPTV Player")
        if hasattr(self, "setStyleSheet"):
            self.setStyleSheet(f"""
                QMainWindow {{ background: {COLORS.background}; }}
                QMenuBar {{
                    background: {COLORS.background};
                    color: {COLORS.text_muted};
                    padding: 6px 10px;
                }}
                QMenuBar::item {{
                    padding: 7px 11px;
                    border-radius: {RADII.sm}px;
                }}
                QMenuBar::item:selected {{
                    background: {COLORS.primary_muted};
                    color: {COLORS.text};
                }}
                QMenu {{
                    background: {COLORS.surface};
                    color: {COLORS.text};
                    border: 1px solid {COLORS.border};
                }}
                QMenu::item {{ padding: 8px 24px 8px 14px; }}
                QMenu::item:selected {{ background: {COLORS.primary_muted}; }}
                QStatusBar {{
                    background: {COLORS.background};
                    color: {COLORS.text_muted};
                    border-top: 1px solid {COLORS.border};
                }}
                """)
        self.add_xtream_provider_action = QAction("Add Xtream Provider…", self)
        self.add_xtream_provider_action.triggered.connect(self.open_xtream_provider_dialog)
        self.add_m3u_provider_action = QAction("Add M3U Provider…", self)
        self.add_m3u_provider_action.triggered.connect(self.open_m3u_provider_dialog)
        self.add_mag_provider_action = QAction("Add MAG/Stalker Provider…", self)
        self.add_mag_provider_action.triggered.connect(self.open_mag_provider_dialog)
        self.browse_channels_action = QAction("Browse Channels", self)
        self.browse_channels_action.triggered.connect(self.open_channel_browser_dialog)
        self.browse_live_categories_action = QAction("Browse Live Categories", self)
        self.browse_live_categories_action.triggered.connect(self.open_category_browser_dialog)
        self.show_epg_action = QAction("Show EPG…", self)
        self.show_epg_action.triggered.connect(self.open_epg_grid_dialog)
        self.xmltv_guide_action = QAction("Configure XMLTV Guide…", self)
        self.xmltv_guide_action.triggered.connect(self.open_xmltv_guide_dialog)
        self.show_provider_list_action = QAction("Show Registered Providers", self)
        self.show_provider_list_action.triggered.connect(self.open_provider_list_dialog)
        self.show_favorites_action = QAction("Favorites…", self)
        self.show_favorites_action.triggered.connect(self.open_favorites_library_dialog)
        self.show_history_action = QAction("History…", self)
        self.show_history_action.triggered.connect(self.open_history_library_dialog)
        self.settings_action = QAction("Settings…", self)
        self.settings_action.triggered.connect(self.open_settings_dialog)
        self.pause_playback_action = QAction("Pause", self)
        self.pause_playback_action.triggered.connect(self._schedule_pause_playback)
        self.resume_playback_action = QAction("Resume", self)
        self.resume_playback_action.triggered.connect(self._schedule_resume_playback)
        self.stop_playback_action = QAction("Stop", self)
        self.stop_playback_action.triggered.connect(self._schedule_stop_playback)
        self.start_recording_action = QAction("Start Recording", self)
        self.start_recording_action.triggered.connect(self._schedule_start_recording)
        self.stop_recording_action = QAction("Stop Recording", self)
        self.stop_recording_action.triggered.connect(self._schedule_stop_recording)
        providers_menu = self.menuBar().addMenu("Providers")
        providers_menu.addAction(self.add_xtream_provider_action)
        providers_menu.addAction(self.add_m3u_provider_action)
        providers_menu.addAction(self.add_mag_provider_action)
        providers_menu.addAction(self.browse_channels_action)
        providers_menu.addAction(self.browse_live_categories_action)
        providers_menu.addAction(self.show_epg_action)
        providers_menu.addAction(self.xmltv_guide_action)
        providers_menu.addAction(self.show_provider_list_action)
        library_menu = self.menuBar().addMenu("Library")
        library_menu.addAction(self.show_favorites_action)
        library_menu.addAction(self.show_history_action)
        playback_menu = self.menuBar().addMenu("Playback")
        playback_menu.addAction(self.pause_playback_action)
        playback_menu.addAction(self.resume_playback_action)
        playback_menu.addAction(self.stop_playback_action)
        playback_menu.addAction(self.start_recording_action)
        playback_menu.addAction(self.stop_recording_action)
        settings_menu = self.menuBar().addMenu("Settings")
        settings_menu.addAction(self.settings_action)
        self._active_xtream_provider_dialog: XtreamProviderDialog | None = None
        self._active_m3u_provider_dialog: M3UProviderDialog | None = None
        self._active_mag_provider_dialog: MAGProviderDialog | None = None
        self._active_channel_browser_dialog: ChannelBrowserDialog | None = None
        self._active_category_browser_dialog: CategoryBrowserDialog | None = None
        self._active_epg_grid_dialog: EPGGridDialog | None = None
        self._active_xmltv_guide_dialog: XMLTVGuideDialog | None = None
        self._active_provider_list_dialog: ProviderListDialog | None = None
        self._active_favorites_library_dialog: FavoritesLibraryDialog | None = None
        self._active_history_library_dialog: HistoryLibraryDialog | None = None
        self._active_settings_dialog: ThemeSettingsDialog | None = None
        self.player_shell: PlayerShell | None = None
        try:
            from samotech_iptv.presentation.player_shell import PlayerShell

            self.player_shell = PlayerShell(
                self.video_surface,
                self._browse_channels,
                self.play_playback_target,
                self._search_registered_channels,
                self._save_favorite,
                self.pause_playback,
                self.resume_playback,
                self.stop_playback,
                self._list_providers,
                self.open_favorites_library_dialog,
                self.open_history_library_dialog,
                self.open_category_browser_dialog,
                self.open_epg_grid_dialog,
                self.open_provider_list_dialog,
                self.open_settings_dialog,
                load_categories=self._load_categories,
                browse_content=self._browse_content,
                load_provider_capabilities=self._load_provider_capabilities,
                load_movie_details=self._load_movie_details,
                load_series_seasons=self._load_series_seasons,
                load_season_episodes=self._load_season_episodes,
                artwork_loader=self._artwork_loader,
                invalidate_pending_playback=self.invalidate_pending_playback,
            )
            self.setCentralWidget(self.player_shell)
        except ImportError:
            # Reduced fake-Qt test doubles do not provide the shell's full widget set.
            self.player_shell = None
            self.setCentralWidget(self.video_surface)

    def open_xtream_provider_dialog(self) -> XtreamProviderDialog:
        """Create and show the secure manual Xtream-entry dialog."""
        from samotech_iptv.presentation.dialogs.xtream_provider_dialog import XtreamProviderDialog

        dialog = XtreamProviderDialog(self._register_xtream_provider)
        dialog.show()
        self._active_xtream_provider_dialog = dialog
        return dialog

    def open_m3u_provider_dialog(self) -> M3UProviderDialog:
        """Create and show the secure manual M3U-entry dialog."""
        from samotech_iptv.presentation.dialogs.m3u_provider_dialog import M3UProviderDialog

        dialog = M3UProviderDialog(self._register_m3u_provider)
        dialog.show()
        self._active_m3u_provider_dialog = dialog
        return dialog

    def open_mag_provider_dialog(self) -> MAGProviderDialog:
        """Create and show the authorized manual MAG/Stalker-entry dialog."""
        from samotech_iptv.presentation.dialogs.mag_provider_dialog import MAGProviderDialog

        dialog = MAGProviderDialog(self._register_mag_provider)
        dialog.show()
        self._active_mag_provider_dialog = dialog
        return dialog

    def open_category_browser_dialog(self) -> CategoryBrowserDialog:
        """Create and show browse-only live categories for a registered provider."""
        from samotech_iptv.presentation.dialogs.category_browser_dialog import (
            CategoryBrowserDialog,
        )

        dialog = CategoryBrowserDialog(self._load_categories)
        dialog.show()
        self._active_category_browser_dialog = dialog
        return dialog

    def open_channel_browser_dialog(self) -> ChannelBrowserDialog:
        """Create and show the credential-safe registered-provider channel browser."""
        from samotech_iptv.presentation.dialogs.channel_browser_dialog import (
            ChannelBrowserDialog,
        )

        dialog = ChannelBrowserDialog(
            self._browse_channels,
            self.play_registered_channel,
            self._search_registered_channels,
            self._save_favorite,
        )
        dialog.show()
        self._active_channel_browser_dialog = dialog
        return dialog

    def open_epg_grid_dialog(self) -> EPGGridDialog:
        """Create and show the credential-safe provider EPG grid."""
        from samotech_iptv.presentation.dialogs.epg_grid_dialog import EPGGridDialog

        dialog = EPGGridDialog(self._load_registered_epg)
        dialog.show()
        self._active_epg_grid_dialog = dialog
        return dialog

    def open_xmltv_guide_dialog(self) -> XMLTVGuideDialog:
        """Create and show local XMLTV binding and manual-refresh controls."""
        from samotech_iptv.presentation.dialogs.xmltv_guide_dialog import XMLTVGuideDialog

        dialog = XMLTVGuideDialog(self._configure_xmltv_binding, self._refresh_xmltv_guide)
        dialog.show()
        self._active_xmltv_guide_dialog = dialog
        return dialog

    def open_provider_list_dialog(self) -> ProviderListDialog:
        """Create and show the credential-safe provider summary dialog."""
        from samotech_iptv.presentation.dialogs.provider_list_dialog import ProviderListDialog

        dialog = ProviderListDialog(
            self._list_providers,
            self._update_provider,
            self._remove_provider,
        )
        dialog.show()
        create_owned_task(dialog, dialog.refresh())
        self._active_provider_list_dialog = dialog
        return dialog

    def open_favorites_library_dialog(self) -> FavoritesLibraryDialog:
        """Create, refresh, and show safe persisted-favorites controls."""
        from samotech_iptv.presentation.dialogs.favorites_library_dialog import (
            FavoritesLibraryDialog,
        )

        dialog = FavoritesLibraryDialog(self._list_favorites, self._remove_favorite)
        dialog.show()
        create_owned_task(dialog, dialog.refresh())
        self._active_favorites_library_dialog = dialog
        return dialog

    def open_history_library_dialog(self) -> HistoryLibraryDialog:
        """Create, refresh, and show existing persisted-history controls."""
        from samotech_iptv.presentation.dialogs.history_library_dialog import HistoryLibraryDialog

        dialog = HistoryLibraryDialog(self._load_history, self._clear_history)
        dialog.show()
        create_owned_task(dialog, dialog.refresh())
        self._active_history_library_dialog = dialog
        return dialog

    def open_settings_dialog(self) -> ThemeSettingsDialog:
        """Create, load, and show the non-secret desktop theme settings dialog."""
        from samotech_iptv.presentation.dialogs.theme_settings_dialog import ThemeSettingsDialog

        dialog = ThemeSettingsDialog(self._load_theme_preference, self._save_theme_preference)
        dialog.show()
        create_owned_task(dialog, dialog.load())
        self._active_settings_dialog = dialog
        return dialog

    def _schedule_pause_playback(self) -> None:
        """Queue playback pause on the supported Qt-aware event loop."""
        create_owned_task(self, self.pause_playback())

    def _schedule_resume_playback(self) -> None:
        """Queue playback resume on the supported Qt-aware event loop."""
        create_owned_task(self, self.resume_playback())

    def _schedule_stop_playback(self) -> None:
        """Queue playback stop on the supported Qt-aware event loop."""
        create_owned_task(self, self.stop_playback())

    def _schedule_start_recording(self) -> None:
        """Queue local stream recording on the supported Qt-aware event loop."""
        create_owned_task(self, self.start_recording())

    def _schedule_stop_recording(self) -> None:
        """Queue recording shutdown on the supported Qt-aware event loop."""
        create_owned_task(self, self.stop_recording())

    async def pause_playback(self) -> None:
        """Pause playback with generic, credential-safe feedback."""
        try:
            await self._pause_playback.execute()
        except Exception:  # noqa: BLE001
            self.statusBar().showMessage("Unable to pause playback")
            return
        self.statusBar().showMessage("Playback paused")

    async def resume_playback(self) -> None:
        """Resume playback with generic, credential-safe feedback."""
        try:
            await self._resume_playback.execute()
        except Exception:  # noqa: BLE001
            self.statusBar().showMessage("Unable to resume playback")
            return
        self.statusBar().showMessage("Playback resumed")

    async def stop_playback(self) -> None:
        """Stop playback with generic, credential-safe feedback."""
        self.invalidate_pending_playback()
        try:
            await self._stop_playback.execute()
        except Exception:  # noqa: BLE001
            self.statusBar().showMessage("Unable to stop playback")
            return
        self.statusBar().showMessage("Playback stopped")

    async def start_recording(self) -> None:
        """Start recording active playback with generic, credential-safe feedback."""
        try:
            await self._start_recording.execute()
        except Exception:  # noqa: BLE001
            self.statusBar().showMessage("Unable to start recording")
            return
        self.statusBar().showMessage("Recording started")

    async def stop_recording(self) -> None:
        """Stop recording active playback with generic, credential-safe feedback."""
        try:
            await self._stop_recording.execute()
        except Exception:  # noqa: BLE001
            self.statusBar().showMessage("Unable to stop recording")
            return
        self.statusBar().showMessage("Recording stopped")

    async def play_registered_channel(self, provider_id: str, channel_id: str) -> None:
        """Attach video output and play one channel from the selected registered provider."""
        self.video_surface.attach_player_output()
        await self._play_registered_channel.execute(provider_id, channel_id)

    async def play_playback_target(self, target: PlaybackTarget) -> PlaybackResult:
        """Attach output and route PlayerShell activation through the target contract."""
        self.video_surface.attach_player_output()
        return await self._play_registered_channel.execute_target(target)

    def invalidate_pending_playback(self) -> None:
        """Invalidate target resolution whenever the visible player context is cleared."""
        invalidate = getattr(self._play_registered_channel, "invalidate_pending_playback", None)
        if callable(invalidate):
            invalidate()
