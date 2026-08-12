"""Credential-safe registration service for manually entered provider profiles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.ports.provider_registration_port import ProviderRegistrationPort
from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import (
        RegisterXtreamProviderRequest,
    )
    from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
    from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

__all__ = ["ProviderRegistrationService"]


class ProviderRegistrationService(ProviderRegistrationPort):
    """Register non-secret provider metadata and delegate secrets to secure storage."""

    def __init__(self, registry: ProviderRegistry, credential_store: CredentialStorePort) -> None:
        self._registry = registry
        self._credential_store = credential_store

    async def register_xtream(self, request: RegisterXtreamProviderRequest) -> str:
        """Register an Xtream profile, retaining its credential only in secure storage."""
        provider_id = ProviderId(request.provider_id)
        if self._registry.find(provider_id.value) is not None:
            raise ValidationError("provider_id", "Provider ID is already registered")
        base_url = URL(request.base_url)
        credential = Credential(request.username, request.password)
        await self._credential_store.store(provider_id, credential)
        self._registry.register(
            InfraProviderMetadata(
                provider_id=provider_id.value,
                provider_type="xtream",
                base_url=base_url.value,
            )
        )
        return provider_id.value
