"""SQLite persistence for non-secret registered-provider metadata."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from samotech_iptv.application.ports.storage_port import StoragePort
from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

__all__ = ["SQLiteProviderMetadataRepository"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS provider_metadata (
    provider_id TEXT PRIMARY KEY,
    provider_type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    capabilities TEXT NOT NULL,
    source_is_secure INTEGER NOT NULL CHECK (source_is_secure IN (0, 1))
)
"""

_UPSERT = """
INSERT INTO provider_metadata (
    provider_id,
    provider_type,
    base_url,
    is_active,
    capabilities,
    source_is_secure
) VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(provider_id) DO UPDATE SET
    provider_type = excluded.provider_type,
    base_url = excluded.base_url,
    is_active = excluded.is_active,
    capabilities = excluded.capabilities,
    source_is_secure = excluded.source_is_secure
"""


class SQLiteProviderMetadataRepository(StoragePort):
    """Persist provider metadata without credentials, tokens, or provider error text."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)

    async def initialise(self) -> None:
        """Create the provider-metadata schema when it does not yet exist."""
        await asyncio.to_thread(self._initialise_sync)

    async def close(self) -> None:
        """Close repository resources; connections are scoped to individual operations."""

    async def save(self, metadata: InfraProviderMetadata) -> None:
        """Create or replace one provider's non-secret metadata."""
        await asyncio.to_thread(self._save_sync, metadata)

    async def list_all(self) -> Sequence[InfraProviderMetadata]:
        """Return all persisted provider metadata in deterministic insertion order."""
        return await asyncio.to_thread(self._list_all_sync)

    async def delete(self, provider_id: str) -> bool:
        """Remove persisted metadata for one provider ID when it exists."""
        return await asyncio.to_thread(self._delete_sync, provider_id)

    async def restore_into(self, registry: ProviderRegistry) -> None:
        """Hydrate an in-memory registry for cataloguing and provider resolution."""
        for metadata in await self.list_all():
            registry.register(metadata)

    def _initialise_sync(self) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self._database_path) as connection:
                connection.execute(_SCHEMA)
        except sqlite3.Error as exc:
            raise StorageError("Unable to initialise provider metadata storage") from exc

    def _save_sync(self, metadata: InfraProviderMetadata) -> None:
        try:
            with sqlite3.connect(self._database_path) as connection:
                connection.execute(
                    _UPSERT,
                    (
                        metadata.provider_id,
                        metadata.provider_type,
                        metadata.base_url,
                        int(metadata.is_active),
                        self._serialize_capabilities(metadata.capabilities),
                        int(metadata.source_is_secure),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageError("Unable to save provider metadata") from exc

    def _list_all_sync(self) -> list[InfraProviderMetadata]:
        try:
            with sqlite3.connect(self._database_path) as connection:
                rows = connection.execute("""
                    SELECT provider_id, provider_type, base_url, is_active, capabilities,
                           source_is_secure
                    FROM provider_metadata
                    ORDER BY rowid
                    """).fetchall()
        except sqlite3.Error as exc:
            raise StorageError("Unable to load provider metadata") from exc
        try:
            return [
                InfraProviderMetadata(
                    provider_id=str(row[0]),
                    provider_type=str(row[1]),
                    base_url=str(row[2]),
                    is_active=bool(row[3]),
                    capabilities=frozenset(
                        ProviderCapability(value) for value in json.loads(str(row[4]))
                    ),
                    source_is_secure=bool(row[5]),
                )
                for row in rows
            ]
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise StorageError("Persisted provider metadata is invalid") from exc

    def _delete_sync(self, provider_id: str) -> bool:
        try:
            with sqlite3.connect(self._database_path) as connection:
                cursor = connection.execute(
                    "DELETE FROM provider_metadata WHERE provider_id = ?",
                    (provider_id,),
                )
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            raise StorageError("Unable to delete provider metadata") from exc

    @staticmethod
    def _serialize_capabilities(capabilities: frozenset[ProviderCapability]) -> str:
        return json.dumps(sorted(capability.value for capability in capabilities))
