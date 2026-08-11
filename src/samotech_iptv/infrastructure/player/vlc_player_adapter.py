"""libVLC implementation of the sole supported player backend."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Protocol

import vlc  # type: ignore[import-not-found]

from samotech_iptv.application.ports.player_port import PlayerPort

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["VlcPlayerAdapter"]


class _VlcInstance(Protocol):
    def media_player_new(self) -> _VlcPlayer: ...

    def media_new(self, url: str) -> object: ...


class _VlcPlayer(Protocol):
    def is_playing(self) -> int: ...

    def set_media(self, media: object) -> None: ...

    def play(self) -> int: ...

    def stop(self) -> None: ...

    def pause(self) -> None: ...


class VlcPlayerAdapter(PlayerPort):
    """Adapt a libVLC media player to the application's player port."""

    def __init__(
        self, instance: _VlcInstance | None = None, player: _VlcPlayer | None = None
    ) -> None:
        self._instance = instance or vlc.Instance()
        self._player = player or self._instance.media_player_new()

    @property
    def is_playing(self) -> bool:
        """Return whether libVLC reports active playback."""
        return bool(self._player.is_playing())

    async def play(self, url: URL) -> None:
        """Load a canonical URL into libVLC and start playback."""
        self._player.set_media(self._instance.media_new(url.value))
        await self._invoke("play")

    async def stop(self) -> None:
        """Stop libVLC playback."""
        await self._invoke("stop")

    async def pause(self) -> None:
        """Pause libVLC playback."""
        await self._invoke("pause")

    async def resume(self) -> None:
        """Resume libVLC playback."""
        await self._invoke("play")

    async def _invoke(self, operation: str) -> None:
        result = await asyncio.to_thread(getattr(self._player, operation))
        if isinstance(result, int) and result < 0:
            raise RuntimeError(f"libVLC {operation} failed")
