"""Resolve registered provider metadata to live channel-catalogue adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.ports.provider_capabilities import CatalogProvider
from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
from samotech_iptv.core.exceptions import ProviderError

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

__all__ = ["ProviderResolutionService"]


class ProviderResolutionService(ProviderResolverPort):
    """Resolve a registered provider while keeping credentials inside infrastructure."""

    def __init__(
        self,
        registry: ProviderRegistry,
        factory: ProviderFactory,
        context: ProviderContext,
    ) -> None:
        self._registry = registry
        self._factory = factory
        self._context = context

    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        """Build the requested provider and verify channel-catalogue support."""
        metadata = self._registry.get(provider_id)
        provider = self._factory.create(metadata, context=self._context)
        if not isinstance(provider, CatalogProvider):
            raise ProviderError("Provider does not support channel browsing")
        return provider
