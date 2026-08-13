"""PySide6 native video surface for the sole libVLC player backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame

if TYPE_CHECKING:
    from PySide6.QtGui import QShowEvent

    from samotech_iptv.application.ports.player_port import PlayerPort

__all__ = ["VlcVideoSurface"]


class VlcVideoSurface(QFrame):
    """A Qt-owned native surface that hosts libVLC video rendering."""

    def __init__(self, player: PlayerPort) -> None:
        super().__init__()
        self._player = player
        self._attached = False
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setStyleSheet("background-color: black;")

    def attach_player_output(self) -> None:
        """Bind libVLC to this widget's platform-native window handle once."""
        if self._attached:
            return
        self._player.attach_video_output(int(self.winId()))
        self._attached = True

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        """Attach output after Qt creates the widget's native window."""
        super().showEvent(event)
        self.attach_player_output()
