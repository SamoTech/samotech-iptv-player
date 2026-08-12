from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.dtos import RecordHistoryRequest
from samotech_iptv.application.use_cases.clear_history import ClearHistory
from samotech_iptv.application.use_cases.record_history import RecordHistory

if TYPE_CHECKING:
    from samotech_iptv.domain.entities.history import History


class FakeHistoryRepository:
    """History repository double for record and clear application behavior."""

    def __init__(self) -> None:
        self.records: list[History] = []
        self.clear_calls = 0

    async def list_recent(self, limit: int = 50) -> list[History]:
        return self.records[:limit]

    async def record(self, history: History) -> None:
        self.records.append(history)

    async def clear(self) -> int:
        self.clear_calls += 1
        cleared = len(self.records)
        self.records.clear()
        return cleared


@pytest.mark.asyncio
async def test_record_history_persists_safe_playback_metadata() -> None:
    repository = FakeHistoryRepository()

    response = await RecordHistory(repository).execute(  # type: ignore[arg-type]
        RecordHistoryRequest(item_id="channel-1", item_type="channel")
    )

    assert response.success is True
    assert [(record.item_id, record.item_type) for record in repository.records] == [
        ("channel-1", "channel")
    ]


@pytest.mark.asyncio
async def test_clear_history_returns_number_of_removed_records() -> None:
    repository = FakeHistoryRepository()
    await RecordHistory(repository).execute(  # type: ignore[arg-type]
        RecordHistoryRequest(item_id="channel-1", item_type="channel")
    )

    response = await ClearHistory(repository).execute()  # type: ignore[arg-type]

    assert response.cleared == 1
    assert response.error is None
    assert repository.clear_calls == 1
