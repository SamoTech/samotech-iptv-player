"""Main Qt application window hosting the native libVLC video surface."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction  # type: ignore[import-not-found]
from PySide6.QtWidgets import QMainWindow  # type: ignore[import-not-found]

from samotech_iptv.presentation.widgets.vlc_video_surface import VlcVideoSurface

if TYPE_CHECKING:
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
    from samotech_iptv.presentation.dialogs.category_browser_dialog import (
        CategoryBrowserDialog,
    )
    from samotech_iptv.presentation.dialogs.channel_browser_dialog import (
        ChannelBrowserDialog,
    )
    from samotech_iptv.presentation.dialogs.epg_grid_dialog import EPGGridDialog
    from samotech_iptv.presentation.dialogs.m3u_provider_dialog import M3UProviderDialog
    from samotech_iptv.presentation.dialogs.mag_provider_dialog import MAGProviderDialog
    from samotech_iptv.presentation.dialogs.provider_list_dialog import ProviderListDialog
    from samotech_iptv.presentation.dialogs.theme_settings_dialog import ThemeSettingsDialog
    from samotech_iptv.presentation.dialogs.xmltv_guide_dialog import XMLTVGuideDialog
    from samotech_iptv.presentation.dialogs.xtream_provider_dialog import XtreamProviderDialog

__all__ = ["MainWindow"]


class MainWindow(QMainWindow):  # type: ignore[misc]
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
        self.video_surface = VlcVideoSurface(player)
        self.setCentralWidget(self.video_surface)
        self.setWindowTitle("SamoTech IPTV Player")
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
        self._active_settings_dialog: ThemeSettingsDialog | None = None

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
        asyncio.create_task(dialog.refresh())
        self._active_provider_list_dialog = dialog
        return dialog

    def open_settings_dialog(self) -> ThemeSettingsDialog:
        """Create, load, and show the non-secret desktop theme settings dialog."""
        from samotech_iptv.presentation.dialogs.theme_settings_dialog import ThemeSettingsDialog

        dialog = ThemeSettingsDialog(self._load_theme_preference, self._save_theme_preference)
        dialog.show()
        asyncio.create_task(dialog.load())
        self._active_settings_dialog = dialog
        return dialog

    def _schedule_pause_playback(self) -> None:
        """Queue playback pause on the supported Qt-aware event loop."""
        asyncio.create_task(self.pause_playback())

    def _schedule_resume_playback(self) -> None:
        """Queue playback resume on the supported Qt-aware event loop."""
        asyncio.create_task(self.resume_playback())

    def _schedule_stop_playback(self) -> None:
        """Queue playback stop on the supported Qt-aware event loop."""
        asyncio.create_task(self.stop_playback())

    def _schedule_start_recording(self) -> None:
        """Queue local stream recording on the supported Qt-aware event loop."""
        asyncio.create_task(self.start_recording())

    def _schedule_stop_recording(self) -> None:
        """Queue recording shutdown on the supported Qt-aware event loop."""
        asyncio.create_task(self.stop_recording())

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
