"""Tests for credential-safe registered-provider lifecycle management."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos.provider_registration import UpdateProviderRequest
from samotech_iptv.application.use_cases.provider_lifecycle import RemoveProvider, UpdateProvider
from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding, XMLTVChannelMapping
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.database.sqlite_provider_metadata_repository import (
    SQLiteProviderMetadataRepository,
)
from samotech_iptv.infrastructure.database.sqlite_xmltv_binding_repository import (
    SQLiteXMLTVBindingRepository,
)
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.provider_registration_service import (
    ProviderRegistrationService,
)
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

if TYPE_CHECKING:
    from pathlib import Path

    from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
    from samotech_iptv.application.ports.provider_registration_port import ProviderRegistrationPort


class FakeCredentialStore:
    """In-memory credential boundary that never exposes values outside assertions."""

    def __init__(self) -> None:
        self._credentials: dict[str, Credential] = {}
        self.store_calls = 0
        self.delete_calls = 0

    async def store(self, provider_id: ProviderId, credential: Credential) -> None:
        self.store_calls += 1
        self._credentials[provider_id.value] = credential

    async def retrieve(self, provider_id: ProviderId) -> Credential | None:
        return self._credentials.get(provider_id.value)

    async def delete(self, provider_id: ProviderId) -> bool:
        self.delete_calls += 1
        return self._credentials.pop(provider_id.value, None) is not None

    async def exists(self, provider_id: ProviderId) -> bool:
        return provider_id.value in self._credentials


class FakeRegistration:
    """Provider lifecycle port double with optional controlled failure."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.update_request: UpdateProviderRequest | None = None
        self.removed_provider_id: str | None = None

    async def update(self, request: UpdateProviderRequest) -> str:
        self.update_request = request
        if self.should_fail:
            raise RuntimeError("sensitive provider failure")
        return request.provider_id

    async def remove(self, provider_id: str) -> str:
        self.removed_provider_id = provider_id
        if self.should_fail:
            raise RuntimeError("sensitive provider failure")
        return provider_id


def _metadata(provider_id: str = "profile") -> InfraProviderMetadata:
    """Build a non-secret Xtream metadata record for lifecycle tests."""
    return InfraProviderMetadata(
        provider_id=provider_id,
        provider_type="xtream",
        base_url="https://old.example.test",
    )


@pytest.mark.asyncio
async def test_remove_provider_deletes_metadata_credentials_and_runtime_registration(
    tmp_path: Path,
) -> None:
    """Removal leaves no persisted or runtime provider profile behind."""
    repository = SQLiteProviderMetadataRepository(tmp_path / "providers.sqlite3")
    await repository.initialise()
    registry = ProviderRegistry()
    metadata = _metadata()
    registry.register(metadata)
    await repository.save(metadata)
    credentials = FakeCredentialStore()
    provider_id = ProviderId("profile")
    test_credential = Credential("user", _password="test-only-secret")  # noqa: S106
    await credentials.store(provider_id, test_credential)
    service = ProviderRegistrationService(
        registry,
        cast("CredentialStorePort", credentials),
        repository,
    )

    response = await RemoveProvider(cast("ProviderRegistrationPort", service)).execute("profile")

    assert response.provider_id == "profile"
    assert response.error is None
    assert registry.find("profile") is None
    assert await repository.list_all() == []
    assert not await credentials.exists(provider_id)
    assert credentials.delete_calls == 1


@pytest.mark.asyncio
async def test_remove_provider_deletes_associated_xmltv_binding(tmp_path: Path) -> None:
    """Provider removal deletes persisted XMLTV mappings along with the profile."""
    metadata_repository = SQLiteProviderMetadataRepository(tmp_path / "providers.sqlite3")
    binding_repository = SQLiteXMLTVBindingRepository(tmp_path / "providers.sqlite3")
    await metadata_repository.initialise()
    await binding_repository.initialise()
    registry = ProviderRegistry()
    metadata = _metadata()
    registry.register(metadata)
    await metadata_repository.save(metadata)
    provider_id = ProviderId("profile")
    await binding_repository.save(
        XMLTVBinding(
            provider_id=provider_id,
            source="/guides/profile.xml",
            mappings=(
                XMLTVChannelMapping(
                    source_channel_id="source.news",
                    channel_id=ChannelId("profile:news"),
                ),
            ),
        )
    )
    credentials = FakeCredentialStore()
    service = ProviderRegistrationService(
        registry,
        cast("CredentialStorePort", credentials),
        metadata_repository,
        binding_repository,
    )

    response = await RemoveProvider(cast("ProviderRegistrationPort", service)).execute("profile")

    assert response.error is None
    assert await binding_repository.load(provider_id) is None


@pytest.mark.asyncio
async def test_update_xtream_preserves_blank_credentials_and_updates_safe_metadata(
    tmp_path: Path,
) -> None:
    """Blank optional edit fields retain the current credential instead of erasing it."""
    repository = SQLiteProviderMetadataRepository(tmp_path / "providers.sqlite3")
    await repository.initialise()
    registry = ProviderRegistry()
    metadata = _metadata()
    registry.register(metadata)
    await repository.save(metadata)
    credentials = FakeCredentialStore()
    provider_id = ProviderId("profile")
    original_credential = Credential("user", _password="test-only-secret")  # noqa: S106
    await credentials.store(provider_id, original_credential)
    credentials.store_calls = 0
    service = ProviderRegistrationService(
        registry,
        cast("CredentialStorePort", credentials),
        repository,
    )

    response = await UpdateProvider(cast("ProviderRegistrationPort", service)).execute(
        UpdateProviderRequest(
            provider_id="profile",
            base_url="https://new.example.test",
            username="",
            password="   ",  # noqa: S106
        )
    )

    assert response.provider_id == "profile"
    assert response.error is None
    assert credentials.store_calls == 0
    assert await credentials.retrieve(provider_id) == original_credential
    assert registry.get("profile").base_url == "https://new.example.test"
    assert (await repository.list_all())[0].base_url == "https://new.example.test"


@pytest.mark.asyncio
async def test_provider_lifecycle_use_cases_return_generic_failure_without_details() -> None:
    """Application failure responses never return provider exception text to presentation."""
    registration = FakeRegistration(should_fail=True)
    update = UpdateProvider(cast("ProviderRegistrationPort", registration))
    remove = RemoveProvider(cast("ProviderRegistrationPort", registration))

    update_response = await update.execute(UpdateProviderRequest(provider_id="profile"))
    remove_response = await remove.execute("profile")

    assert update_response.error == "Unable to update provider"
    assert remove_response.error == "Unable to remove provider"
    assert "sensitive" not in update_response.error
    assert "sensitive" not in remove_response.error
