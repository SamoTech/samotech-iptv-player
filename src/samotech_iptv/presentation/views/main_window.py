"""Initial PySide6 main window for VLC-backed IPTV playback."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow  # type: ignore[import-not-found]

from samotech_iptv.presentation.dialogs.xtream_provider_dialog import XtreamProviderDialog
from samotech_iptv.presentation.widgets.vlc_video_surface import VlcVideoSurface

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.use_cases.play_channel import PlayChannel
    from samotech_iptv.application.use_cases.register_xtream_provider import (
        RegisterXtreamProvider,
    )

__all__ = ["MainWindow"]


class MainWindow(QMainWindow):  # type: ignore[misc]
    """Own the Qt video surface and delegate playback to application orchestration."""

    def __init__(
        self,
        player: PlayerPort,
        play_channel: PlayChannel,
        register_xtream_provider: RegisterXtreamProvider,
    ) -> None:
        super().__init__()
        self._play_channel = play_channel
        self._register_xtream_provider = register_xtream_provider
        self.video_surface = VlcVideoSurface(player)
        self.setCentralWidget(self.video_surface)
        self.setWindowTitle("SamoTech IPTV Player")

    def open_xtream_provider_dialog(self) -> XtreamProviderDialog:
        """Create and show the secure manual Xtream-entry dialog."""
        dialog = XtreamProviderDialog(self._register_xtream_provider)
        dialog.show()
        return dialog

    async def play_channel(self, channel_id: str) -> None:
        """Resolve and start one provider channel through the application boundary."""
        self.video_surface.attach_player_output()
        await self._play_channel.execute(channel_id)
