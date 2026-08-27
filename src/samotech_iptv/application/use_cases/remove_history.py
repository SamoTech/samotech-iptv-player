"""Remove one persisted playback-history record through the application boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import RemoveHistoryResponse

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories.history_repository import HistoryRepository

__all__ = ["RemoveHistory"]


class RemoveHistory:
    """Delete one history record by its opaque history identifier."""

    def __init__(self, repository: HistoryRepository) -> None:
        self._repository = repository

    async def execute(self, history_id: str) -> RemoveHistoryResponse:
        """Remove the requested history record."""
        try:
            removed = await self._repository.delete(history_id)
        except Exception:  # noqa: BLE001
            return RemoveHistoryResponse(removed=False, error="Unable to remove history")
        return RemoveHistoryResponse(removed=removed)
