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
        now = datetime.now(UTC)
        started_at = self._parse_datetime(request.started_at, now)
        updated_at = self._parse_datetime(request.updated_at, now)
        duration_seconds = max(0, request.duration_seconds)
        position_seconds = max(0, request.position_seconds)
        if duration_seconds > 0:
            position_seconds = min(position_seconds, duration_seconds)
            watched_percentage = min(100.0, max(0.0, position_seconds / duration_seconds * 100))
        else:
            watched_percentage = 0.0
        completed = bool(
            request.completed and request.item_type in {"movie", "episode"} and duration_seconds > 0
        ) or (
            request.item_type in {"movie", "episode"}
            and duration_seconds > 0
            and position_seconds >= duration_seconds
        )
        if completed:
            position_seconds = duration_seconds
            watched_percentage = 100.0
        provider_key = request.provider_id or "<legacy>"
        history_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"samotech-history:{provider_key}:{request.item_type}:{request.item_id}",
            )
        )
        history = History(
            id=history_id,
            item_id=request.item_id,
            item_type=request.item_type,
            watched_at=updated_at,
            provider_id=request.provider_id,
            started_at=started_at,
            updated_at=updated_at,
            duration_seconds=duration_seconds,
            position_seconds=position_seconds,
            watched_percentage=watched_percentage,
            completed=completed,
        )
        try:
            await self._repository.record(history)
        except Exception:  # noqa: BLE001
            return RecordHistoryResponse(success=False, error="Unable to record history")
        return RecordHistoryResponse(success=True)

    @staticmethod
    def _parse_datetime(value: str | None, fallback: datetime) -> datetime:
        if value is None:
            return fallback
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Invalid history timestamp") from exc
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
