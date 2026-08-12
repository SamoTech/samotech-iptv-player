"""Stop a local recording through the sole player backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort

__all__ = ["StopRecording"]


class StopRecording:
    """Delegate recording shutdown to the active player without handling stream URLs."""

    def __init__(self, player: PlayerPort) -> None:
        self._player = player

    async def execute(self) -> None:
        """Stop active recording while allowing the player to continue playback."""
        await self._player.stop_recording()
