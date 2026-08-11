"""M3U provider adapter composed from source loading and canonical parsing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.ports.provider_capabilities import (
    CapabilityProvider,
    CatalogProvider,
    SearchProvider,
)
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.parsing.m3u_parser import M3UParser
from samotech_iptv.infrastructure.parsing.m3u_source_loader import (
    M3USourceLoader,
    M3USourceLoaderPort,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["M3UProviderAdapter", "register_m3u_with_factory"]

_CAPABILITIES = frozenset({ProviderCapability.LIVE, ProviderCapability.SEARCH})


class M3UProviderAdapter(CatalogProvider, SearchProvider, CapabilityProvider):
    """Load local or remote M3U content into the canonical live-channel catalogue."""

    def __init__(
        self,
        metadata: InfraProviderMetadata,
        context: ProviderContext,
        source_loader: M3USourceLoaderPort | None = None,
        parser: M3UParser | None = None,
    ) -> None:
        self._metadata = metadata
        self._source = metadata.base_url
        self._source_loader = source_loader or M3USourceLoader(context.http_client)
        self._parser = parser or M3UParser()

    @property
    def provider_id(self) -> ProviderId:
        """Return the registered provider identity."""
        return ProviderId(self._metadata.provider_id)

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        """Return only capabilities executable by the current M3U adapter."""
        return _CAPABILITIES

    async def load_channels(self) -> Sequence[Channel]:
        """Load source text then translate it through the canonical M3U parser."""
        source_text = await self._source_loader.load(self._source)
        return self._parser.parse(source_text, self.provider_id).channels

    async def search_channels(self, query: str, limit: int = 100) -> Sequence[Channel]:
        """Search the loaded M3U catalogue locally."""
        if limit <= 0:
            return []
        normalized_query = query.strip().casefold()
        channels = await self.load_channels()
        return [
            channel
            for channel in channels
            if not normalized_query or normalized_query in channel.name.casefold()
        ][:limit]


def _build_m3u_adapter(
    metadata: InfraProviderMetadata,
    context: ProviderContext,
    source_loader: M3USourceLoaderPort | None = None,
) -> M3UProviderAdapter:
    return M3UProviderAdapter(metadata, context, source_loader=source_loader)


def register_m3u_with_factory(factory: ProviderFactory) -> None:
    """Register M3U adapter construction with the application-owned factory."""
    factory.register_type("m3u", _build_m3u_adapter)
