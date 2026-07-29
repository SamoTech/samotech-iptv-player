"""Repository interfaces — abstract contracts for persistence.

Concrete implementations live in ``infrastructure.database``.
The application layer depends only on these interfaces.

All methods are async to support both in-memory (test) and
async-database (production) implementations without change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from samotech_iptv.domain.entities import (
    Channel,
    EPGEntry,
    Favorite,
    History,
    Playlist,
    Provider,
)
from samotech_iptv.domain.value_objects import ChannelId, ProviderId

__all__ = [
    "ChannelRepository",
    "PlaylistRepository",
    "ProviderRepository",
    "EPGRepository",
    "HistoryRepository",
    "FavoriteRepository",
]


class ChannelRepository(ABC):
    """CRUD contract for Channel aggregates."""

    @abstractmethod
    async def get_by_id(self, channel_id: ChannelId) -> Optional[Channel]: ...

    @abstractmethod
    async def list_by_provider(self, provider_id: ProviderId) -> Sequence[Channel]: ...

    @abstractmethod
    async def list_by_category(self, category_id: str) -> Sequence[Channel]: ...

    @abstractmethod
    async def search(self, query: str, limit: int = 100) -> Sequence[Channel]: ...

    @abstractmethod
    async def upsert(self, channel: Channel) -> None: ...

    @abstractmethod
    async def delete_by_provider(self, provider_id: ProviderId) -> int: ...


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


class ProviderRepository(ABC):
    """CRUD contract for Provider aggregates."""

    @abstractmethod
    async def get_by_id(self, provider_id: ProviderId) -> Optional[Provider]: ...

    @abstractmethod
    async def list_active(self) -> Sequence[Provider]: ...

    @abstractmethod
    async def save(self, provider: Provider) -> None: ...

    @abstractmethod
    async def delete(self, provider_id: ProviderId) -> bool: ...


class EPGRepository(ABC):
    """CRUD contract for EPGEntry aggregates."""

    @abstractmethod
    async def list_by_channel(
        self, channel_id: ChannelId, limit: int = 48
    ) -> Sequence[EPGEntry]: ...

    @abstractmethod
    async def upsert(self, entry: EPGEntry) -> None: ...

    @abstractmethod
    async def purge_stale(self) -> int: ...


class HistoryRepository(ABC):
    """CRUD contract for playback History records."""

    @abstractmethod
    async def list_recent(self, limit: int = 50) -> Sequence[History]: ...

    @abstractmethod
    async def record(self, history: History) -> None: ...

    @abstractmethod
    async def clear(self) -> int: ...


class FavoriteRepository(ABC):
    """CRUD contract for Favorite records."""

    @abstractmethod
    async def list_all(self) -> Sequence[Favorite]: ...

    @abstractmethod
    async def save(self, favorite: Favorite) -> None: ...

    @abstractmethod
    async def delete(self, favorite_id: str) -> bool: ...
