from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.domain.entities.history import History
from samotech_iptv.infrastructure.database.sqlite_history_repository import (
    SQLiteHistoryRepository,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.asyncio
async def test_sqlite_history_repository_round_trips_progress_fields(tmp_path: Path) -> None:
    repository = SQLiteHistoryRepository(tmp_path / "history.sqlite3")
    started = datetime(2026, 8, 12, 0, 0, tzinfo=UTC)
    updated = datetime(2026, 8, 12, 0, 30, tzinfo=UTC)
    history = History(
        id="history-1",
        item_id="movie-1",
        item_type="movie",
        watched_at=updated,
        duration_seconds=120,
        position_seconds=120,
        provider_id="provider-a",
        started_at=started,
        updated_at=updated,
        watched_percentage=100.0,
        completed=True,
    )

    await repository.initialise()
    await repository.record(history)

    assert await repository.list_recent() == [history]


@pytest.mark.asyncio
async def test_sqlite_history_repository_records_lists_and_clears_history(tmp_path: Path) -> None:
    repository = SQLiteHistoryRepository(tmp_path / "history.sqlite3")
    history = History(
        id="history-1",
        item_id="channel-1",
        item_type="channel",
        watched_at=datetime(2026, 8, 12, tzinfo=UTC),
    )

    await repository.initialise()
    await repository.record(history)

    assert await repository.list_recent() == [history]
    assert await repository.clear() == 1
    assert await repository.list_recent() == []


@pytest.mark.asyncio
async def test_sqlite_history_repository_deletes_one_record_by_id(tmp_path: Path) -> None:
    repository = SQLiteHistoryRepository(tmp_path / "history.sqlite3")
    first = History(
        id="history-1",
        item_id="movie-1",
        item_type="movie",
        watched_at=datetime(2026, 8, 12, tzinfo=UTC),
    )
    second = History(
        id="history-2",
        item_id="movie-2",
        item_type="movie",
        watched_at=datetime(2026, 8, 11, tzinfo=UTC),
    )

    await repository.initialise()
    await repository.record(first)
    await repository.record(second)

    assert await repository.delete("history-1") is True
    assert await repository.delete("history-1") is False
    assert await repository.list_recent() == [second]
