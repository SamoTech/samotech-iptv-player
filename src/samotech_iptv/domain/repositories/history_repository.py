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
