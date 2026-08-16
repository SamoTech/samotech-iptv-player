"""Application contract for the sole libVLC-backed media player."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from samotech_iptv.application.dtos.playback import ResolvedPlayback

__all__ = ["PlayerPort"]


class PlayerPort(ABC):
    """Contract for the libVLC media-player backend."""

    @abstractmethod
    async def play(self, playback: ResolvedPlayback) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def pause(self) -> None: ...

    @abstractmethod
    async def resume(self) -> None: ...

    @abstractmethod
    async def start_recording(self, destination: Path) -> None:
        """Start recording the active stream to a local destination."""
        ...

    @abstractmethod
    async def stop_recording(self) -> None:
        """Stop recording while continuing active playback."""
        ...

    @abstractmethod
    def attach_video_output(self, native_window_id: int) -> None:
        """Attach video rendering to a presentation-owned native window."""
        ...

    @property
    @abstractmethod
    def is_playing(self) -> bool: ...

    @property
    @abstractmethod
    def is_recording(self) -> bool:
        """Return whether the active stream is currently being recorded."""
        ...
