"""Capability-oriented Xtream live-channel provider adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.ports.provider_capabilities import (
    AuthenticationProvider,
    CapabilityProvider,
    CatalogProvider,
    SearchProvider,
)
from samotech_iptv.core.exceptions import AuthenticationError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.xtream_api_client import XtreamApiClient
from samotech_iptv.infrastructure.providers.xtream_domain_translator import XtreamDomainTranslator
from samotech_iptv.infrastructure.providers.xtream_request_builder import XtreamRequestBuilder

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["XtreamProviderAdapter", "register_xtream_with_factory"]

_CAPABILITIES = frozenset(
    {ProviderCapability.AUTHENTICATION, ProviderCapability.LIVE, ProviderCapability.SEARCH}
)


class XtreamProviderAdapter(
    AuthenticationProvider, CatalogProvider, SearchProvider, CapabilityProvider
):
    """Retrieve and translate Xtream live channels through canonical boundaries."""

    def __init__(self, metadata: InfraProviderMetadata, context: ProviderContext) -> None:
        self._metadata = metadata
        self._context = context
        self._authenticated = False

    @property
    def provider_id(self) -> ProviderId:
        """Return the registered provider identity."""
        return ProviderId(self._metadata.provider_id)

    @property
    def is_authenticated(self) -> bool:
        """Return the result of the latest authentication attempt."""
        return self._authenticated

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        """Advertise only executable authentication, live-catalogue, and search support."""
        return _CAPABILITIES

    async def authenticate(self, credential: Credential) -> bool:
        """Validate credentials remotely before storing them in the configured credential store."""
        client = self._client_for(credential)
        self._authenticated = await client.authenticate()
        if self._authenticated:
            await self._context.credential_store.store(self.provider_id, credential)
        return self._authenticated

    async def load_channels(self) -> Sequence[Channel]:
        """Retrieve the stored credential and translate Xtream live DTOs into channels."""
        client = await self._stored_client()
        return [
            XtreamDomainTranslator.channel(record, self.provider_id)
            for record in await client.live_streams()
        ]

    async def search_channels(self, query: str, limit: int = 100) -> Sequence[Channel]:
        """Search retrieved canonical live channels locally without exposing provider DTOs."""
        if limit <= 0:
            return []
        normalized_query = query.strip().casefold()
        return [
            channel
            for channel in await self.load_channels()
            if not normalized_query or normalized_query in channel.name.casefold()
        ][:limit]

    async def _stored_client(self) -> XtreamApiClient:
        credential = await self._context.credential_store.retrieve(self.provider_id)
        if credential is None:
            raise AuthenticationError("Xtream credentials are not available")
        return self._client_for(credential)

    def _client_for(self, credential: Credential) -> XtreamApiClient:
        builder = XtreamRequestBuilder(URL(self._metadata.base_url), credential)
        return XtreamApiClient(self._context.http_client, builder)


def _build_xtream_adapter(
    metadata: InfraProviderMetadata, context: ProviderContext
) -> XtreamProviderAdapter:
    return XtreamProviderAdapter(metadata, context)


def register_xtream_with_factory(factory: ProviderFactory) -> None:
    """Register Xtream construction with the application-owned provider factory."""
    factory.register_type("xtream", _build_xtream_adapter)
