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
    provider_id TEXT,
    started_at TEXT,
    updated_at TEXT,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    position_seconds INTEGER NOT NULL DEFAULT 0,
    watched_percentage REAL NOT NULL DEFAULT 0,
    completed INTEGER NOT NULL DEFAULT 0
)
"""
_MIGRATION_COLUMNS = {
    "provider_id": "TEXT",
    "started_at": "TEXT",
    "updated_at": "TEXT",
    "watched_percentage": "REAL NOT NULL DEFAULT 0",
    "completed": "INTEGER NOT NULL DEFAULT 0",
}


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
                columns = {
                    str(row[1])
                    for row in connection.execute("PRAGMA table_info(watch_history)").fetchall()
                }
                for name, definition in _MIGRATION_COLUMNS.items():
                    if name not in columns:
                        connection.execute(
                            f"ALTER TABLE watch_history ADD COLUMN {name} {definition}"
                        )
                connection.execute("""
                    UPDATE watch_history
                    SET watched_percentage = CASE
                            WHEN duration_seconds > 0 THEN MIN(
                                100.0,
                                MAX(0.0, position_seconds * 100.0 / duration_seconds)
                            )
                            ELSE 0.0
                        END
                    WHERE watched_percentage = 0
                    """)
        except sqlite3.Error as exc:
            raise StorageError("Unable to initialise history storage") from exc

    def _list_recent_sync(self, limit: int) -> list[History]:
        try:
            with sqlite_connection(self._database_path) as connection:
                rows = connection.execute(
                    """
                    SELECT id, item_id, item_type, watched_at, provider_id, started_at,
                           updated_at, duration_seconds, position_seconds,
                           watched_percentage, completed
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
                    provider_id=str(row[4]) if row[4] is not None else None,
                    started_at=self._parse_optional_datetime(row[5]),
                    updated_at=self._parse_optional_datetime(row[6]),
                    duration_seconds=int(row[7]),
                    position_seconds=int(row[8]),
                    watched_percentage=float(row[9]),
                    completed=bool(row[10]),
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
                    INSERT INTO watch_history
                    (id, item_id, item_type, watched_at, provider_id, started_at, updated_at,
                     duration_seconds, position_seconds, watched_percentage, completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        watched_at = excluded.watched_at,
                        provider_id = excluded.provider_id,
                        started_at = COALESCE(watch_history.started_at, excluded.started_at),
                        updated_at = excluded.updated_at,
                        duration_seconds = excluded.duration_seconds,
                        position_seconds = excluded.position_seconds,
                        watched_percentage = excluded.watched_percentage,
                        completed = excluded.completed
                    """,
                    (
                        history.id,
                        history.item_id,
                        history.item_type,
                        history.watched_at.isoformat(),
                        history.provider_id,
                        history.started_at.isoformat() if history.started_at is not None else None,
                        history.updated_at.isoformat() if history.updated_at is not None else None,
                        history.duration_seconds,
                        history.position_seconds,
                        history.watched_percentage,
                        int(history.completed),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageError("Unable to record history") from exc

    @staticmethod
    def _parse_optional_datetime(value: object) -> datetime | None:
        return datetime.fromisoformat(str(value)) if value is not None else None

    def _clear_sync(self) -> int:
        try:
            with sqlite_connection(self._database_path) as connection:
                cursor = connection.execute("DELETE FROM watch_history")
                return cursor.rowcount
        except sqlite3.Error as exc:
            raise StorageError("Unable to clear history") from exc
