"""SQLite persistence for local XMLTV source bindings and explicit channel mappings."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding, XMLTVChannelMapping
from samotech_iptv.domain.repositories.xmltv_binding_repository import XMLTVBindingRepository
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.infrastructure.database.sqlite_connection import sqlite_connection

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["SQLiteXMLTVBindingRepository"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS xmltv_bindings (
    provider_id TEXT PRIMARY KEY,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS xmltv_channel_mappings (
    provider_id TEXT NOT NULL,
    source_channel_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    PRIMARY KEY (provider_id, source_channel_id),
    FOREIGN KEY (provider_id) REFERENCES xmltv_bindings(provider_id) ON DELETE CASCADE
)
"""


class SQLiteXMLTVBindingRepository(XMLTVBindingRepository):
    """Persist non-secret local XMLTV sources without programme data or credentials."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)

    async def initialise(self) -> None:
        """Create XMLTV source-binding storage when it does not yet exist."""
        await asyncio.to_thread(self._initialise_sync)

    async def load(self, provider_id: ProviderId) -> XMLTVBinding | None:
        """Return one configured source binding and its explicit mappings."""
        return await asyncio.to_thread(self._load_sync, provider_id)

    async def save(self, binding: XMLTVBinding) -> None:
        """Replace one provider's binding and mappings in one SQLite transaction."""
        await asyncio.to_thread(self._save_sync, binding)

    async def delete(self, provider_id: ProviderId) -> bool:
        """Remove one binding and its mappings when it exists."""
        return await asyncio.to_thread(self._delete_sync, provider_id)

    def _initialise_sync(self) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite_connection(self._database_path, foreign_keys=True) as connection:
                connection.executescript(_SCHEMA)
        except sqlite3.Error as exc:
            raise StorageError("Unable to initialise XMLTV binding storage") from exc

    def _load_sync(self, provider_id: ProviderId) -> XMLTVBinding | None:
        try:
            with sqlite_connection(self._database_path, foreign_keys=True) as connection:
                row = connection.execute(
                    "SELECT source FROM xmltv_bindings WHERE provider_id = ?",
                    (provider_id.value,),
                ).fetchone()
                if row is None:
                    return None
                mapping_rows = connection.execute(
                    """
                    SELECT source_channel_id, channel_id
                    FROM xmltv_channel_mappings
                    WHERE provider_id = ?
                    ORDER BY source_channel_id
                    """,
                    (provider_id.value,),
                ).fetchall()
            return XMLTVBinding(
                provider_id=provider_id,
                source=str(row[0]),
                mappings=tuple(
                    XMLTVChannelMapping(
                        source_channel_id=str(mapping_row[0]),
                        channel_id=ChannelId(str(mapping_row[1])),
                    )
                    for mapping_row in mapping_rows
                ),
            )
        except (sqlite3.Error, ValueError) as exc:
            raise StorageError("Unable to load XMLTV binding") from exc

    def _save_sync(self, binding: XMLTVBinding) -> None:
        try:
            with sqlite_connection(self._database_path, foreign_keys=True) as connection:
                connection.execute(
                    """
                    INSERT INTO xmltv_bindings (provider_id, source)
                    VALUES (?, ?)
                    ON CONFLICT(provider_id) DO UPDATE SET source = excluded.source
                    """,
                    (binding.provider_id.value, binding.source),
                )
                connection.execute(
                    "DELETE FROM xmltv_channel_mappings WHERE provider_id = ?",
                    (binding.provider_id.value,),
                )
                connection.executemany(
                    """
                    INSERT INTO xmltv_channel_mappings (provider_id, source_channel_id, channel_id)
                    VALUES (?, ?, ?)
                    """,
                    [
                        (
                            binding.provider_id.value,
                            mapping.source_channel_id,
                            mapping.channel_id.value,
                        )
                        for mapping in binding.mappings
                    ],
                )
        except sqlite3.Error as exc:
            raise StorageError("Unable to save XMLTV binding") from exc

    def _delete_sync(self, provider_id: ProviderId) -> bool:
        try:
            with sqlite_connection(self._database_path, foreign_keys=True) as connection:
                cursor = connection.execute(
                    "DELETE FROM xmltv_bindings WHERE provider_id = ?",
                    (provider_id.value,),
                )
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            raise StorageError("Unable to delete XMLTV binding") from exc
