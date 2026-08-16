from __future__ import annotations

from datetime import UTC, datetime

import pytest

from samotech_iptv.application.dtos import LoadHistoryRequest, RecordHistoryRequest
from samotech_iptv.application.use_cases.clear_history import ClearHistory
from samotech_iptv.application.use_cases.load_history import LoadHistory
from samotech_iptv.application.use_cases.record_history import RecordHistory
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
    assert repository.records[0].duration_seconds == 0
    assert repository.records[0].position_seconds == 0


@pytest.mark.asyncio
async def test_record_history_computes_provider_scoped_progress_and_completion() -> None:
    repository = FakeHistoryRepository()

    response = await RecordHistory(repository).execute(  # type: ignore[arg-type]
        RecordHistoryRequest(
            item_id="movie-1",
            item_type="movie",
            provider_id="provider-a",
            duration_seconds=100,
            position_seconds=40,
        )
    )

    assert response.success is True
    record = repository.records[0]
    assert record.provider_id == "provider-a"
    assert record.watched_percentage == 40.0
    assert record.completed is False
    assert record.started_at is not None
    assert record.updated_at is not None


@pytest.mark.asyncio
async def test_record_history_never_completes_live_unknown_duration() -> None:
    repository = FakeHistoryRepository()

    await RecordHistory(repository).execute(  # type: ignore[arg-type]
        RecordHistoryRequest(
            item_id="channel-1",
            item_type="channel",
            provider_id="provider-a",
            duration_seconds=0,
            position_seconds=90,
            completed=True,
        )
    )

    record = repository.records[0]
    assert record.completed is False
    assert record.watched_percentage == 0.0
    assert record.position_seconds == 90


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


@pytest.mark.asyncio
async def test_load_history_exposes_existing_canonical_progress_values() -> None:
    repository = FakeHistoryRepository()
    repository.records.append(
        History(
            id="history-1",
            item_id="channel-1",
            item_type="channel",
            watched_at=datetime(2026, 8, 13, tzinfo=UTC),
            duration_seconds=120,
            position_seconds=30,
        )
    )

    response = await LoadHistory(repository).execute(LoadHistoryRequest())  # type: ignore[arg-type]

    assert response.error is None
    assert [
        (item.item_id, item.duration_seconds, item.position_seconds) for item in response.items
    ] == [("channel-1", 120, 30)]


@pytest.mark.asyncio
async def test_load_history_returns_generic_failure_without_storage_details() -> None:
    class FailingHistoryRepository(FakeHistoryRepository):
        async def list_recent(self, limit: int = 50) -> list[History]:
            raise RuntimeError("private storage path unavailable")

    response = await LoadHistory(FailingHistoryRepository()).execute(LoadHistoryRequest())  # type: ignore[arg-type]

    assert response.items == []
    assert response.error == "Unable to load history"
    assert "private" not in response.error
