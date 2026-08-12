"""Application boundary for resolving registered providers by identifier."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import CatalogProvider

__all__ = ["ProviderResolverPort"]


class ProviderResolverPort(ABC):
    """Resolve a registered provider to its channel-catalogue capability."""

    @abstractmethod
    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        """Return the resolved provider without exposing implementation details or secrets."""
        ...
