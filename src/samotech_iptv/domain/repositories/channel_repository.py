"""ChannelRepository — abstract CRUD contract for Channel aggregates."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["ChannelRepository"]


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
