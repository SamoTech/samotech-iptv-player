from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.dtos.provider_registration import (
    RegisterM3UProviderRequest,
)
from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.infrastructure.database.sqlite_provider_metadata_repository import (
    SQLiteProviderMetadataRepository,
)
from samotech_iptv.infrastructure.providers.provider_metadata import (
    InfraProviderMetadata,
)
from samotech_iptv.infrastructure.providers.provider_registration_service import (
    ProviderRegistrationService,
)
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

if TYPE_CHECKING:
    from pathlib import Path

    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.domain.value_objects.provider_id import ProviderId


class FakeCredentialStore(CredentialStorePort):
    """Credential-store double retaining values separately from SQLite metadata."""

    def __init__(self) -> None:
        self.credentials: dict[str, Credential] = {}

    async def store(self, provider_id: ProviderId, credential: Credential) -> None:
        self.credentials[provider_id.value] = credential

    async def retrieve(self, provider_id: ProviderId) -> Credential | None:
        return self.credentials.get(provider_id.value)

    async def delete(self, provider_id: ProviderId) -> bool:
        return self.credentials.pop(provider_id.value, None) is not None


@pytest.mark.asyncio
async def test_sqlite_repository_round_trips_non_secret_provider_metadata(tmp_path: Path) -> None:
    database_path = tmp_path / "providers.sqlite3"
    repository = SQLiteProviderMetadataRepository(database_path)
    metadata = InfraProviderMetadata(
        provider_id="m3u-demo",
        provider_type="m3u",
        base_url="https://example.invalid/playlist.m3u",
        is_active=False,
        capabilities=frozenset({ProviderCapability.LIVE, ProviderCapability.SEARCH}),
        last_error="Provider returned a sensitive URL",
        source_is_secure=True,
    )

    await repository.initialise()
    await repository.save(metadata)

    stored = await repository.list_all()

    assert stored == [
        InfraProviderMetadata(
            provider_id="m3u-demo",
            provider_type="m3u",
            base_url="https://example.invalid/playlist.m3u",
            is_active=False,
            capabilities=frozenset({ProviderCapability.LIVE, ProviderCapability.SEARCH}),
            source_is_secure=True,
        )
    ]
    with closing(sqlite3.connect(database_path)) as connection:
        column_names = {
            row[1] for row in connection.execute("PRAGMA table_info(provider_metadata)")
        }
    assert "last_error" not in column_names
    assert "credential" not in column_names
    assert "password" not in column_names


@pytest.mark.asyncio
async def test_registration_persists_sanitized_m3u_metadata_and_restores_registry(
    tmp_path: Path,
) -> None:
    repository = SQLiteProviderMetadataRepository(tmp_path / "providers.sqlite3")
    await repository.initialise()
    registry = ProviderRegistry()
    credential_store = FakeCredentialStore()
    registration = ProviderRegistrationService(registry, credential_store, repository)

    await registration.register_m3u(
        RegisterM3UProviderRequest(
            provider_id="secure-m3u",
            source="https://example.invalid/playlist.m3u?token=opaque-token",
        )
    )

    persisted = await repository.list_all()
    restored_registry = ProviderRegistry()
    await repository.restore_into(restored_registry)

    assert registry.get("secure-m3u").source_is_secure is True
    assert persisted[0].base_url == "https://example.invalid/playlist.m3u"
    assert persisted[0].source_is_secure is True
    assert persisted[0].last_error is None
    assert restored_registry.get("secure-m3u") == persisted[0]
    assert credential_store.credentials["secure-m3u"].password.endswith("opaque-token")


@pytest.mark.asyncio
async def test_sqlite_repository_upserts_then_deletes_provider_metadata(tmp_path: Path) -> None:
    repository = SQLiteProviderMetadataRepository(tmp_path / "providers.sqlite3")
    await repository.initialise()
    await repository.save(
        InfraProviderMetadata(
            provider_id="demo",
            provider_type="m3u",
            base_url="https://example.invalid/first.m3u",
        )
    )
    await repository.save(
        InfraProviderMetadata(
            provider_id="demo",
            provider_type="m3u",
            base_url="https://example.invalid/second.m3u",
            is_active=False,
        )
    )

    assert (await repository.list_all())[0].base_url.endswith("second.m3u")
    assert (await repository.delete("demo")) is True
    assert (await repository.delete("demo")) is False
    assert await repository.list_all() == []
