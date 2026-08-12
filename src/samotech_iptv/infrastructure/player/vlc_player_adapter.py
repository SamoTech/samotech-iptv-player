"""libVLC implementation of the sole supported player backend."""

from __future__ import annotations

import asyncio
import sys
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

    def set_xwindow(self, native_window_id: int) -> None: ...

    def set_hwnd(self, native_window_id: int) -> None: ...

    def set_nsobject(self, native_window_id: int) -> None: ...


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

    def attach_video_output(self, native_window_id: int) -> None:
        """Attach libVLC rendering to a Qt-owned native video surface."""
        if native_window_id <= 0:
            raise ValueError("native_window_id must be positive")
        if sys.platform.startswith("linux"):
            self._player.set_xwindow(native_window_id)
        elif sys.platform == "win32":
            self._player.set_hwnd(native_window_id)
        elif sys.platform == "darwin":
            self._player.set_nsobject(native_window_id)
        else:
            raise RuntimeError(f"Unsupported libVLC video-output platform: {sys.platform}")

    async def _invoke(self, operation: str) -> None:
        result = await asyncio.to_thread(getattr(self._player, operation))
        if isinstance(result, int) and result < 0:
            raise RuntimeError(f"libVLC {operation} failed")
