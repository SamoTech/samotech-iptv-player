"""Main Qt application window hosting the native libVLC video surface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction  # type: ignore[import-not-found]
from PySide6.QtWidgets import QMainWindow  # type: ignore[import-not-found]

from samotech_iptv.presentation.widgets.vlc_video_surface import VlcVideoSurface

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
    from samotech_iptv.application.use_cases.list_providers import ListProviders
    from samotech_iptv.application.use_cases.play_channel import PlayChannel
    from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider
    from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider
    from samotech_iptv.application.use_cases.register_xtream_provider import (
        RegisterXtreamProvider,
    )
    from samotech_iptv.presentation.dialogs.channel_browser_dialog import (
        ChannelBrowserDialog,
    )
    from samotech_iptv.presentation.dialogs.m3u_provider_dialog import M3UProviderDialog
    from samotech_iptv.presentation.dialogs.mag_provider_dialog import MAGProviderDialog
    from samotech_iptv.presentation.dialogs.provider_list_dialog import ProviderListDialog
    from samotech_iptv.presentation.dialogs.xtream_provider_dialog import XtreamProviderDialog

__all__ = ["MainWindow"]


class MainWindow(QMainWindow):  # type: ignore[misc]
    """Own the Qt video surface and delegate playback to application orchestration."""

    def __init__(
        self,
        player: PlayerPort,
        play_channel: PlayChannel,
        register_xtream_provider: RegisterXtreamProvider,
        register_m3u_provider: RegisterM3UProvider,
        register_mag_provider: RegisterMAGProvider,
        list_providers: ListProviders,
        browse_channels: BrowseChannels,
    ) -> None:
        super().__init__()
        self._play_channel = play_channel
        self._register_xtream_provider = register_xtream_provider
        self._register_m3u_provider = register_m3u_provider
        self._register_mag_provider = register_mag_provider
        self._list_providers = list_providers
        self._browse_channels = browse_channels
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
        self.show_provider_list_action = QAction("Show Registered Providers", self)
        self.show_provider_list_action.triggered.connect(self.open_provider_list_dialog)
        providers_menu = self.menuBar().addMenu("Providers")
        providers_menu.addAction(self.add_xtream_provider_action)
        providers_menu.addAction(self.add_m3u_provider_action)
        providers_menu.addAction(self.add_mag_provider_action)
        providers_menu.addAction(self.browse_channels_action)
        providers_menu.addAction(self.show_provider_list_action)
        self._active_xtream_provider_dialog: XtreamProviderDialog | None = None
        self._active_m3u_provider_dialog: M3UProviderDialog | None = None
        self._active_mag_provider_dialog: MAGProviderDialog | None = None
        self._active_channel_browser_dialog: ChannelBrowserDialog | None = None
        self._active_provider_list_dialog: ProviderListDialog | None = None

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

    def open_channel_browser_dialog(self) -> ChannelBrowserDialog:
        """Create and show the credential-safe registered-provider channel browser."""
        from samotech_iptv.presentation.dialogs.channel_browser_dialog import (
            ChannelBrowserDialog,
        )

        dialog = ChannelBrowserDialog(self._browse_channels)
        dialog.show()
        self._active_channel_browser_dialog = dialog
        return dialog

    def open_provider_list_dialog(self) -> ProviderListDialog:
        """Create and show the credential-safe provider summary dialog."""
        from samotech_iptv.presentation.dialogs.provider_list_dialog import ProviderListDialog

        dialog = ProviderListDialog(self._list_providers)
        dialog.show()
        self._active_provider_list_dialog = dialog
        return dialog

    async def play_channel(self, channel_id: str) -> None:
        """Resolve and start one provider channel through the application boundary."""
        self.video_surface.attach_player_output()
        await self._play_channel.execute(channel_id)
