"""HistoryRepository — abstract CRUD contract for History records."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.history import History

__all__ = ["HistoryRepository"]


class HistoryRepository(ABC):
    """CRUD contract for playback History records."""

    @abstractmethod
    async def list_recent(self, limit: int = 50) -> Sequence[History]: ...

    @abstractmethod
    async def record(self, history: History) -> None: ...

    @abstractmethod
    async def clear(self) -> int: ...

    @abstractmethod
    async def delete(self, history_id: str) -> bool: ...

    async def find_latest(
        self,
        *,
        provider_id: str | None,
        item_id: str,
        item_type: str,
    ) -> History | None:
        """Find the newest provider-scoped record without requiring a schema extension in fakes."""
        records = await self.list_recent(limit=500)
        for record in records:
            if (
                record.provider_id == provider_id
                and record.item_id == item_id
                and record.item_type == item_type
            ):
                return record
        return None
