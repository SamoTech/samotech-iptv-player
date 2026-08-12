"""Generic pause, resume, and stop controls for the sole player backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort

__all__ = ["PausePlayback", "ResumePlayback", "StopPlayback"]


class PausePlayback:
    """Pause the current player session without exposing media details."""

    def __init__(self, player: PlayerPort) -> None:
        self._player = player

    async def execute(self) -> None:
        """Delegate a pause request to the configured player backend."""
        await self._player.pause()


class ResumePlayback:
    """Resume the current player session without exposing media details."""

    def __init__(self, player: PlayerPort) -> None:
        self._player = player

    async def execute(self) -> None:
        """Delegate a resume request to the configured player backend."""
        await self._player.resume()


class StopPlayback:
    """Stop the current player session without exposing media details."""

    def __init__(self, player: PlayerPort) -> None:
        self._player = player

    async def execute(self) -> None:
        """Delegate a stop request to the configured player backend."""
        await self._player.stop()
