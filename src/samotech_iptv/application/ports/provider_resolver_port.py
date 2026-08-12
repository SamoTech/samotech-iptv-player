"""Application boundary for resolving registered providers by identifier."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import (
        CatalogProvider,
        PlaybackProvider,
    )

__all__ = ["ProviderResolverPort"]


class ProviderResolverPort(ABC):
    """Resolve a registered provider to its channel-catalogue capability."""

    @abstractmethod
    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        """Return a channel-catalogue provider without exposing secrets."""
        ...

    @abstractmethod
    def resolve_playback_provider(self, provider_id: str) -> PlaybackProvider:
        """Return a stream-resolution provider without exposing secrets."""
        ...
