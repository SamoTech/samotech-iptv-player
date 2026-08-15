"""SQLite persistence for the non-secret desktop theme preference."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from samotech_iptv.application.ports.theme_preference_repository import ThemePreferenceRepository
from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.domain.value_objects.theme_preference import ThemePreference
from samotech_iptv.infrastructure.database.sqlite_connection import sqlite_connection

__all__ = ["SQLiteThemePreferenceRepository"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS theme_preference (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    preference TEXT NOT NULL
)
"""


class SQLiteThemePreferenceRepository(ThemePreferenceRepository):
    """Persist a single validated theme preference without user credentials or provider data."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)

    async def initialise(self) -> None:
        """Create the settings schema when it does not already exist."""
        await asyncio.to_thread(self._initialise_sync)

    async def load(self) -> ThemePreference:
        """Return the persisted preference or the system default when none was saved."""
        return await asyncio.to_thread(self._load_sync)

    async def save(self, preference: ThemePreference) -> None:
        """Persist one validated preference."""
        await asyncio.to_thread(self._save_sync, preference)

    def _initialise_sync(self) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite_connection(self._database_path) as connection:
                connection.execute(_SCHEMA)
        except sqlite3.Error as exc:
            raise StorageError("Unable to initialise theme settings") from exc

    def _load_sync(self) -> ThemePreference:
        try:
            with sqlite_connection(self._database_path) as connection:
                connection.execute(_SCHEMA)
                row = connection.execute(
                    "SELECT preference FROM theme_preference WHERE id = 1"
                ).fetchone()
            return ThemePreference(str(row[0])) if row is not None else ThemePreference.SYSTEM
        except (sqlite3.Error, ValueError) as exc:
            raise StorageError("Unable to load theme settings") from exc

    def _save_sync(self, preference: ThemePreference) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite_connection(self._database_path) as connection:
                connection.execute(_SCHEMA)
                connection.execute(
                    "INSERT OR REPLACE INTO theme_preference (id, preference) VALUES (1, ?)",
                    (preference.value,),
                )
        except sqlite3.Error as exc:
            raise StorageError("Unable to save theme settings") from exc
