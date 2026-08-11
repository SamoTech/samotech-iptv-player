"""PlayerPort — media player backend contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["PlayerPort"]


class PlayerPort(ABC):
    """Contract for the media-player backend (MPV, VLC, WinRT, …)."""

    @abstractmethod
    async def play(self, url: URL) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def pause(self) -> None: ...

    @abstractmethod
    async def resume(self) -> None: ...

    @property
    @abstractmethod
    def is_playing(self) -> bool: ...
