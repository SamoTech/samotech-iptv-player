"""Credential-safe registration service for manually entered provider profiles."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from samotech_iptv.application.ports.provider_registration_port import ProviderRegistrationPort
from samotech_iptv.core.exceptions import NotFoundError, StorageError, ValidationError
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import (
        RegisterM3UProviderRequest,
        RegisterMAGProviderRequest,
        RegisterXtreamProviderRequest,
        UpdateProviderRequest,
    )
    from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
    from samotech_iptv.domain.repositories.xmltv_binding_repository import XMLTVBindingRepository
    from samotech_iptv.infrastructure.database.sqlite_provider_metadata_repository import (
        SQLiteProviderMetadataRepository,
    )
    from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

__all__ = ["ProviderRegistrationService"]

_MAG_DEVICE_IDENTITY_MARKER = "mag-device-identity"


class ProviderRegistrationService(ProviderRegistrationPort):
    """Register non-secret provider metadata and delegate secrets to secure storage."""

    def __init__(
        self,
        registry: ProviderRegistry,
        credential_store: CredentialStorePort,
        metadata_repository: SQLiteProviderMetadataRepository | None = None,
        xmltv_binding_repository: XMLTVBindingRepository | None = None,
    ) -> None:
        self._registry = registry
        self._credential_store = credential_store
        self._metadata_repository = metadata_repository
        self._xmltv_binding_repository = xmltv_binding_repository

    async def register_mag(self, request: RegisterMAGProviderRequest) -> str:
        """Register a MAG/Stalker portal while retaining its MAC only in secure storage."""
        provider_id = ProviderId(request.provider_id)
        if self._registry.find(provider_id.value) is not None:
            raise ValidationError("provider_id", "Provider ID is already registered")
        portal_url = URL(request.portal_url)
        credential = Credential(username=request.mac_address, _password=_MAG_DEVICE_IDENTITY_MARKER)
        await self._credential_store.store(provider_id, credential)
        await self._persist_metadata(
            InfraProviderMetadata(
                provider_id=provider_id.value,
                provider_type="mag",
                base_url=portal_url.value,
            )
        )
        return provider_id.value

    async def register_m3u(self, request: RegisterM3UProviderRequest) -> str:
        """Register an M3U source without retaining tokens in provider metadata."""
        provider_id = ProviderId(request.provider_id)
        if self._registry.find(provider_id.value) is not None:
            raise ValidationError("provider_id", "Provider ID is already registered")
        source = request.source.strip()
        if not source:
            raise ValidationError("source", "M3U source must not be blank")
        metadata_source, credential = self._m3u_metadata_source(source)
        source_is_secure = credential is not None
        if credential is not None:
            await self._credential_store.store(provider_id, credential)
        await self._persist_metadata(
            InfraProviderMetadata(
                provider_id=provider_id.value,
                provider_type="m3u",
                base_url=metadata_source,
                source_is_secure=source_is_secure,
            )
        )
        return provider_id.value

    @staticmethod
    def _m3u_metadata_source(source: str) -> tuple[str, Credential | None]:
        """Return safe metadata plus an optional secure credential containing the full source."""
        parsed = urlsplit(source)
        if parsed.scheme.casefold() not in {"http", "https"}:
            return source, None
        validated_source = URL(source)
        if not (parsed.username or parsed.password or parsed.query or parsed.fragment):
            return validated_source.value, None
        netloc = parsed.hostname or ""
        if parsed.port is not None:
            netloc = f"{netloc}:{parsed.port}"
        return (
            urlunsplit((parsed.scheme, netloc, parsed.path, "", "")),
            Credential(username="m3u-source", _password=validated_source.value),
        )

    async def register_xtream(self, request: RegisterXtreamProviderRequest) -> str:
        """Register an Xtream profile, retaining its credential only in secure storage."""
        provider_id = ProviderId(request.provider_id)
        if self._registry.find(provider_id.value) is not None:
            raise ValidationError("provider_id", "Provider ID is already registered")
        base_url = URL(request.base_url)
        credential = Credential(request.username, request.password)
        await self._credential_store.store(provider_id, credential)
        await self._persist_metadata(
            InfraProviderMetadata(
                provider_id=provider_id.value,
                provider_type="xtream",
                base_url=base_url.value,
            )
        )
        return provider_id.value

    async def update(self, request: UpdateProviderRequest) -> str:
        """Update one profile without replacing credentials supplied as blank values."""
        provider_id = ProviderId(request.provider_id)
        existing = self._registry.find(provider_id.value)
        if existing is None:
            raise NotFoundError("Provider", provider_id.value)
        if existing.provider_type == "m3u":
            return await self._update_m3u(provider_id, existing, request)
        if existing.provider_type == "mag":
            return await self._update_mag(provider_id, existing, request)
        if existing.provider_type == "xtream":
            return await self._update_xtream(provider_id, existing, request)
        raise ValidationError("provider_type", "Provider type cannot be updated")

    async def remove(self, provider_id: str) -> str:
        """Remove one profile from persistence, keyring, and the runtime registry."""
        validated_provider_id = ProviderId(provider_id)
        existing = self._registry.find(validated_provider_id.value)
        if existing is None:
            raise NotFoundError("Provider", validated_provider_id.value)
        binding = None
        if self._xmltv_binding_repository is not None:
            binding = await self._xmltv_binding_repository.load(validated_provider_id)
        if self._metadata_repository is not None:
            deleted = await self._metadata_repository.delete(validated_provider_id.value)
            if not deleted:
                raise StorageError("Provider metadata is unavailable")
        try:
            if self._xmltv_binding_repository is not None and binding is not None:
                await self._xmltv_binding_repository.delete(validated_provider_id)
            await self._credential_store.delete(validated_provider_id)
        except Exception:
            await self._restore_metadata_after_failed_removal(existing)
            if self._xmltv_binding_repository is not None and binding is not None:
                await self._xmltv_binding_repository.save(binding)
            raise
        self._registry.deregister(validated_provider_id.value)
        return validated_provider_id.value

    async def _update_m3u(
        self,
        provider_id: ProviderId,
        existing: InfraProviderMetadata,
        request: UpdateProviderRequest,
    ) -> str:
        """Replace an M3U source only when a non-blank replacement is supplied."""
        if request.source is None:
            return provider_id.value
        source = request.source.strip()
        if not source:
            raise ValidationError("source", "M3U source must not be blank")
        metadata_source, credential = self._m3u_metadata_source(source)
        if credential is None and existing.source_is_secure:
            await self._credential_store.delete(provider_id)
        if credential is not None:
            await self._credential_store.store(provider_id, credential)
        await self._persist_metadata(
            replace(
                existing,
                base_url=metadata_source,
                source_is_secure=credential is not None,
            )
        )
        return provider_id.value

    async def _update_mag(
        self,
        provider_id: ProviderId,
        existing: InfraProviderMetadata,
        request: UpdateProviderRequest,
    ) -> str:
        """Update MAG non-secret portal metadata and only an explicitly supplied MAC."""
        if request.mac_address is not None and request.mac_address.strip():
            await self._credential_store.store(
                provider_id,
                Credential(
                    username=request.mac_address.strip(), _password=_MAG_DEVICE_IDENTITY_MARKER
                ),
            )
        base_url = existing.base_url if request.base_url is None else URL(request.base_url).value
        await self._persist_metadata(replace(existing, base_url=base_url))
        return provider_id.value

    async def _update_xtream(
        self,
        provider_id: ProviderId,
        existing: InfraProviderMetadata,
        request: UpdateProviderRequest,
    ) -> str:
        """Update Xtream metadata and retain omitted or blank credential fields unchanged."""
        username = request.username.strip() if request.username is not None else ""
        password = request.password.strip() if request.password is not None else ""
        if username or password:
            existing_credential = await self._credential_store.retrieve(provider_id)
            if existing_credential is None:
                raise StorageError("Provider credential is unavailable")
            await self._credential_store.store(
                provider_id,
                Credential(
                    username=username or existing_credential.username,
                    _password=password or existing_credential.password,
                ),
            )
        base_url = existing.base_url if request.base_url is None else URL(request.base_url).value
        await self._persist_metadata(replace(existing, base_url=base_url))
        return provider_id.value

    async def _restore_metadata_after_failed_removal(self, metadata: InfraProviderMetadata) -> None:
        """Best-effort rollback after a keyring deletion failure; never log provider details."""
        if self._metadata_repository is not None:
            await self._metadata_repository.save(metadata)

    async def _persist_metadata(self, metadata: InfraProviderMetadata) -> None:
        """Persist non-secret metadata before exposing the provider to runtime resolution."""
        if self._metadata_repository is not None:
            await self._metadata_repository.save(metadata)
        self._registry.register(metadata)
