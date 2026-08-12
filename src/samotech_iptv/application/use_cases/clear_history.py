"""Clear persisted playback history through the application boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import ClearHistoryResponse

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories.history_repository import HistoryRepository

__all__ = ["ClearHistory"]


class ClearHistory:
    """Remove all persisted watch-history records."""

    def __init__(self, repository: HistoryRepository) -> None:
        self._repository = repository

    async def execute(self) -> ClearHistoryResponse:
        """Clear all history records and return the number removed."""
        try:
            cleared = await self._repository.clear()
        except Exception:  # noqa: BLE001
            return ClearHistoryResponse(cleared=0, error="Unable to clear history")
        return ClearHistoryResponse(cleared=cleared)
