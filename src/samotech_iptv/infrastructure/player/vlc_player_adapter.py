"""libVLC-backed implementation of playback and active-stream recording."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Protocol

import vlc  # type: ignore[import-not-found]

from samotech_iptv.application.ports.player_port import PlayerPort

if TYPE_CHECKING:
    from pathlib import Path

    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["VlcPlayerAdapter"]


class _VlcMedia(Protocol):
    def add_option(self, option: str) -> None: ...


class _VlcInstance(Protocol):
    def media_player_new(self) -> _VlcPlayer: ...

    def media_new(self, url: str) -> _VlcMedia: ...


class _VlcPlayer(Protocol):
    def is_playing(self) -> int: ...

    def set_media(self, media: _VlcMedia) -> None: ...

    def play(self) -> int: ...

    def stop(self) -> None: ...

    def pause(self) -> None: ...

    def set_xwindow(self, native_window_id: int) -> None: ...

    def set_hwnd(self, native_window_id: int) -> None: ...

    def set_nsobject(self, native_window_id: int) -> None: ...


class VlcPlayerAdapter(PlayerPort):
    """Adapt the sole libVLC media player to application playback and recording operations."""

    def __init__(
        self, instance: _VlcInstance | None = None, player: _VlcPlayer | None = None
    ) -> None:
        self._instance = instance or vlc.Instance()
        self._player = player or self._instance.media_player_new()
        self._current_url: URL | None = None
        self._recording_destination: Path | None = None

    @property
    def is_playing(self) -> bool:
        """Return whether libVLC reports active playback."""
        return bool(self._player.is_playing())

    @property
    def is_recording(self) -> bool:
        """Return whether the active libVLC media contains a recording output."""
        return self._recording_destination is not None

    async def play(self, url: URL) -> None:
        """Load a canonical URL into libVLC and start playback without recording."""
        await self._set_media_and_play(url)
        self._current_url = url
        self._recording_destination = None

    async def stop(self) -> None:
        """Stop libVLC playback and terminate any active recording output."""
        await self._invoke("stop")
        self._recording_destination = None

    async def pause(self) -> None:
        """Pause libVLC playback while preserving an active recording configuration."""
        await self._invoke("pause")

    async def resume(self) -> None:
        """Resume libVLC playback while preserving an active recording configuration."""
        await self._invoke("play")

    async def start_recording(self, destination: Path) -> None:
        """Restart active media with one libVLC display/file duplicate stream output."""
        if self._current_url is None or not self.is_playing:
            raise RuntimeError("Cannot record without active playback")
        if self._recording_destination is not None:
            raise RuntimeError("Recording is already active")
        output_path = destination.expanduser().resolve()
        if output_path.suffix.lower() != ".ts":
            raise ValueError("Recording destination must use the .ts extension")
        if output_path.exists():
            raise FileExistsError("Recording destination already exists")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        media = self._instance.media_new(self._current_url.value)
        media.add_option(self._recording_option(output_path))
        self._player.set_media(media)
        await self._invoke("play")
        self._recording_destination = output_path

    async def stop_recording(self) -> None:
        """Restart active media without stream output while continuing normal playback."""
        if self._recording_destination is None or self._current_url is None:
            raise RuntimeError("No active recording")
        await self._set_media_and_play(self._current_url)
        self._recording_destination = None

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

    async def _set_media_and_play(self, url: URL) -> None:
        self._player.set_media(self._instance.media_new(url.value))
        await self._invoke("play")

    @staticmethod
    def _recording_option(destination: Path) -> str:
        value = str(destination)
        if any(character in value for character in ("\x00", "\n", "\r")):
            raise ValueError("Recording destination contains unsupported characters")
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f":sout=#duplicate{{dst=display,dst=std{{access=file,mux=ts,dst='{escaped}'}}}}"

    async def _invoke(self, operation: str) -> None:
        result = await asyncio.to_thread(getattr(self._player, operation))
        if isinstance(result, int) and result < 0:
            raise RuntimeError(f"libVLC {operation} failed")
