"""Resolve registered provider metadata to live channel-catalogue adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.ports.provider_capabilities import (
    CapabilityProvider,
    CatalogProvider,
    CategoryProvider,
    EPGProvider,
    EpisodePlaybackProvider,
    MoviePlaybackProvider,
    PlaybackProvider,
    SearchProvider,
    SeriesDetailProvider,
    SeriesProvider,
    VodProvider,
)
from samotech_iptv.application.ports.provider_content_resolver_port import (
    ProviderContentResolverPort,
)
from samotech_iptv.application.ports.provider_non_live_resolver_port import (
    ProviderNonLivePlaybackResolverPort,
    ProviderSeriesDiscoveryResolverPort,
)
from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.infrastructure.providers.provider_runtime_cache import ProviderRuntimeCache

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

__all__ = ["ProviderResolutionService"]


class ProviderResolutionService(
    ProviderResolverPort,
    ProviderContentResolverPort,
    ProviderNonLivePlaybackResolverPort,
    ProviderSeriesDiscoveryResolverPort,
):
    """Resolve a registered provider while keeping credentials inside infrastructure."""

    def __init__(
        self,
        registry: ProviderRegistry,
        factory: ProviderFactory,
        context: ProviderContext,
        runtime_cache: ProviderRuntimeCache | None = None,
    ) -> None:
        self._registry = registry
        self._factory = factory
        self._context = context
        self._runtime_cache = runtime_cache or ProviderRuntimeCache(factory, context)

    @property
    def runtime_cache(self) -> ProviderRuntimeCache:
        """Return the live-provider owner for lifecycle composition and shutdown."""
        return self._runtime_cache

    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        """Build the requested provider and verify channel-catalogue support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, CatalogProvider):
            raise ProviderError("Provider does not support channel browsing")
        return provider

    def resolve_category_provider(self, provider_id: str) -> CategoryProvider:
        """Build the requested provider and verify live-category support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, CategoryProvider):
            raise ProviderError("Provider does not support category browsing")
        return provider

    def resolve_playback_provider(self, provider_id: str) -> PlaybackProvider:
        """Build the requested provider and verify stream-resolution support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, PlaybackProvider):
            raise ProviderError("Provider does not support playback")
        return provider

    def resolve_movie_playback_provider(self, provider_id: str) -> MoviePlaybackProvider:
        """Build the provider and verify explicit movie-resolution support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, MoviePlaybackProvider) or not self._advertises(
            provider, ProviderCapability.MOVIE_PLAYBACK
        ):
            raise ProviderError("Provider does not support movie playback")
        return provider

    def resolve_episode_playback_provider(self, provider_id: str) -> EpisodePlaybackProvider:
        """Build the provider and verify explicit episode-resolution support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, EpisodePlaybackProvider) or not self._advertises(
            provider, ProviderCapability.EPISODE_PLAYBACK
        ):
            raise ProviderError("Provider does not support episode playback")
        return provider

    def resolve_search_provider(self, provider_id: str) -> SearchProvider:
        """Build the requested provider and verify channel-search support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, SearchProvider):
            raise ProviderError("Provider does not support channel search")
        return provider

    def resolve_epg_provider(self, provider_id: str) -> EPGProvider:
        """Build the requested provider and verify EPG support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, EPGProvider):
            raise ProviderError("Provider does not support EPG")
        return provider

    def resolve_vod_provider(self, provider_id: str) -> VodProvider:
        """Build the requested provider and verify VOD catalogue support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, VodProvider):
            raise ProviderError("Provider does not support VOD browsing")
        return provider

    def resolve_series_provider(self, provider_id: str) -> SeriesProvider:
        """Build the requested provider and verify series catalogue support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, SeriesProvider):
            raise ProviderError("Provider does not support series browsing")
        return provider

    def resolve_series_detail_provider(self, provider_id: str) -> SeriesDetailProvider:
        """Build the provider and verify explicit Series-detail discovery support."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, SeriesDetailProvider) or not self._advertises(
            provider, ProviderCapability.SERIES_DETAILS
        ):
            raise ProviderError("Provider does not support series details")
        return provider

    def resolve_capability_provider(self, provider_id: str) -> CapabilityProvider:
        """Build the requested provider and read its executable capability declaration."""
        provider = self._resolve(provider_id)
        if not isinstance(provider, CapabilityProvider):
            raise ProviderError("Provider does not expose capabilities")
        return provider

    def _resolve(self, provider_id: str) -> object:
        """Create a provider only after locating its registered non-secret metadata."""
        metadata = self._registry.get(provider_id)
        return self._runtime_cache.get_or_create(metadata)

    @staticmethod
    def _advertises(provider: object, capability: ProviderCapability) -> bool:
        """Require the exact runtime declaration for a new non-live capability."""
        return (
            isinstance(provider, CapabilityProvider)
            and capability in provider.supported_capabilities()
        )
