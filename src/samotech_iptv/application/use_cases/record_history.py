"""Record one playback-history item through the application boundary."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import RecordHistoryRequest, RecordHistoryResponse
from samotech_iptv.domain.entities.history import History

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories.history_repository import HistoryRepository

__all__ = ["RecordHistory"]


class RecordHistory:
    """Persist a safe playback-history record after media playback starts."""

    def __init__(self, repository: HistoryRepository) -> None:
        self._repository = repository

    async def execute(self, request: RecordHistoryRequest) -> RecordHistoryResponse:
        """Record canonical content identifiers and playback position metadata only."""
        history = History(
            id=str(uuid.uuid4()),
            item_id=request.item_id,
            item_type=request.item_type,
            watched_at=datetime.now(UTC),
            duration_seconds=request.duration_seconds,
            position_seconds=request.position_seconds,
        )
        try:
            await self._repository.record(history)
        except Exception:  # noqa: BLE001
            return RecordHistoryResponse(success=False, error="Unable to record history")
        return RecordHistoryResponse(success=True)
