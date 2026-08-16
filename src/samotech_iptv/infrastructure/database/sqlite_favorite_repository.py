"""SQLite-backed persistence for user favourite records."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.domain.entities.favorite import Favorite
from samotech_iptv.domain.repositories.favorite_repository import FavoriteRepository
from samotech_iptv.infrastructure.database.sqlite_connection import sqlite_connection

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["SQLiteFavoriteRepository"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS favorites (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    added_at TEXT NOT NULL,
    provider_id TEXT
)
"""


class SQLiteFavoriteRepository(FavoriteRepository):
    """Persist favourites without storing credentials, stream URLs, or provider secrets."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)

    async def initialise(self) -> None:
        """Create the favourites schema when it does not already exist."""
        await asyncio.to_thread(self._initialise_sync)

    async def list_all(self) -> Sequence[Favorite]:
        """Return favourites newest first."""
        return await asyncio.to_thread(self._list_all_sync)

    async def save(self, favorite: Favorite) -> None:
        """Persist one favourite record."""
        await asyncio.to_thread(self._save_sync, favorite)

    async def delete(self, favorite_id: str) -> bool:
        """Delete a favourite by identifier and return whether it existed."""
        return await asyncio.to_thread(self._delete_sync, favorite_id)

    def _initialise_sync(self) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite_connection(self._database_path) as connection:
                connection.execute(_SCHEMA)
                columns = {
                    str(row[1])
                    for row in connection.execute("PRAGMA table_info(favorites)").fetchall()
                }
                if "provider_id" not in columns:
                    connection.execute("ALTER TABLE favorites ADD COLUMN provider_id TEXT")
        except sqlite3.Error as exc:
            raise StorageError("Unable to initialise favorites storage") from exc

    def _list_all_sync(self) -> list[Favorite]:
        try:
            with sqlite_connection(self._database_path) as connection:
                rows = connection.execute(
                    "SELECT id, item_id, item_type, added_at, provider_id "
                    "FROM favorites ORDER BY added_at DESC"
                ).fetchall()
            return [
                Favorite(
                    id=str(row[0]),
                    item_id=str(row[1]),
                    item_type=str(row[2]),
                    added_at=datetime.fromisoformat(str(row[3])),
                    provider_id=None if row[4] is None else str(row[4]),
                )
                for row in rows
            ]
        except (sqlite3.Error, ValueError) as exc:
            raise StorageError("Unable to load favorites") from exc

    def _save_sync(self, favorite: Favorite) -> None:
        try:
            with sqlite_connection(self._database_path) as connection:
                connection.execute(
                    """
                    INSERT INTO favorites (id, item_id, item_type, added_at, provider_id)
                    SELECT ?, ?, ?, ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM favorites
                        WHERE item_id = ?
                          AND item_type = ?
                          AND (
                              provider_id = ?
                              OR (provider_id IS NULL AND ? IS NULL)
                          )
                    )
                    """,
                    (
                        favorite.id,
                        favorite.item_id,
                        favorite.item_type,
                        favorite.added_at.isoformat(),
                        favorite.provider_id,
                        favorite.item_id,
                        favorite.item_type,
                        favorite.provider_id,
                        favorite.provider_id,
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageError("Unable to save favorite") from exc

    def _delete_sync(self, favorite_id: str) -> bool:
        try:
            with sqlite_connection(self._database_path) as connection:
                cursor = connection.execute("DELETE FROM favorites WHERE id = ?", (favorite_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            raise StorageError("Unable to delete favorite") from exc
