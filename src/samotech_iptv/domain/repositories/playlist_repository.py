"""PlaylistRepository — abstract CRUD contract for Playlist aggregates."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from samotech_iptv.domain.entities.playlist import Playlist

__all__ = ["PlaylistRepository"]


class PlaylistRepository(ABC):
    """CRUD contract for Playlist aggregates."""

    @abstractmethod
    async def get_by_id(self, playlist_id: str) -> Optional[Playlist]: ...

    @abstractmethod
    async def list_all(self) -> Sequence[Playlist]: ...

    @abstractmethod
    async def save(self, playlist: Playlist) -> None: ...

    @abstractmethod
    async def delete(self, playlist_id: str) -> bool: ...
