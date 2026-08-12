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
