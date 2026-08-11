"""EPGRepository — abstract CRUD contract for EPGEntry aggregates."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.value_objects.channel_id import ChannelId

__all__ = ["EPGRepository"]


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
