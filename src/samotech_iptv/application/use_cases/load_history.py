"""LoadHistory use-case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import (
    HistoryItemDTO,
    LoadHistoryRequest,
    LoadHistoryResponse,
)
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories import HistoryRepository

_log = get_logger("use_cases.load_history")
_ERROR = "Unable to load history"


class LoadHistory:
    """Load recent playback history records."""

    def __init__(self, repository: HistoryRepository) -> None:
        self._repo = repository

    async def execute(self, request: LoadHistoryRequest) -> LoadHistoryResponse:
        _log.info("Loading history (limit=%d)", request.limit)
        try:
            items = await self._repo.list_recent(limit=request.limit)
        except Exception:  # noqa: BLE001
            _log.error("Unable to load history")
            return LoadHistoryResponse(error=_ERROR)
        dtos = [
            HistoryItemDTO(
                id=h.id,
                item_id=h.item_id,
                item_type=h.item_type,
                watched_at=h.watched_at.isoformat(),
                duration_seconds=h.duration_seconds,
                position_seconds=h.position_seconds,
            )
            for h in items
        ]
        return LoadHistoryResponse(items=dtos)
