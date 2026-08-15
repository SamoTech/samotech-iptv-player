"""SQLite-backed persistence for playback-history records."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.domain.entities.history import History
from samotech_iptv.domain.repositories.history_repository import HistoryRepository
from samotech_iptv.infrastructure.database.sqlite_connection import sqlite_connection

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["SQLiteHistoryRepository"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS watch_history (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    watched_at TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    position_seconds INTEGER NOT NULL
)
"""


class SQLiteHistoryRepository(HistoryRepository):
    """Persist playback history without provider credentials or stream URLs."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)

    async def initialise(self) -> None:
        """Create the watch-history schema when it does not already exist."""
        await asyncio.to_thread(self._initialise_sync)

    async def list_recent(self, limit: int = 50) -> Sequence[History]:
        """Return recent history records newest first."""
        return await asyncio.to_thread(self._list_recent_sync, limit)

    async def record(self, history: History) -> None:
        """Persist one playback-history record."""
        await asyncio.to_thread(self._record_sync, history)

    async def clear(self) -> int:
        """Remove all persisted history and return the count removed."""
        return await asyncio.to_thread(self._clear_sync)

    def _initialise_sync(self) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite_connection(self._database_path) as connection:
                connection.execute(_SCHEMA)
        except sqlite3.Error as exc:
            raise StorageError("Unable to initialise history storage") from exc

    def _list_recent_sync(self, limit: int) -> list[History]:
        try:
            with sqlite_connection(self._database_path) as connection:
                rows = connection.execute(
                    """
                    SELECT id, item_id, item_type, watched_at, duration_seconds, position_seconds
                    FROM watch_history
                    ORDER BY watched_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [
                History(
                    id=str(row[0]),
                    item_id=str(row[1]),
                    item_type=str(row[2]),
                    watched_at=datetime.fromisoformat(str(row[3])),
                    duration_seconds=int(row[4]),
                    position_seconds=int(row[5]),
                )
                for row in rows
            ]
        except (sqlite3.Error, ValueError) as exc:
            raise StorageError("Unable to load history") from exc

    def _record_sync(self, history: History) -> None:
        try:
            with sqlite_connection(self._database_path) as connection:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO watch_history
                    (id, item_id, item_type, watched_at, duration_seconds, position_seconds)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        history.id,
                        history.item_id,
                        history.item_type,
                        history.watched_at.isoformat(),
                        history.duration_seconds,
                        history.position_seconds,
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageError("Unable to record history") from exc

    def _clear_sync(self) -> int:
        try:
            with sqlite_connection(self._database_path) as connection:
                cursor = connection.execute("DELETE FROM watch_history")
                return cursor.rowcount
        except sqlite3.Error as exc:
            raise StorageError("Unable to clear history") from exc
