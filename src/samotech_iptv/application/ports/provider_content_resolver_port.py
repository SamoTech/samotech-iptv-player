"""Optional resolver boundary for registered non-live provider capabilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import (
        CapabilityProvider,
        SeriesProvider,
        VodProvider,
    )

__all__ = ["ProviderContentResolverPort"]


class ProviderContentResolverPort(ABC):
    """Resolve only optional content capabilities without exposing credentials."""

    @abstractmethod
    def resolve_vod_provider(self, provider_id: str) -> VodProvider:
        """Return a VOD-capable provider or raise a controlled provider error."""
        ...

    @abstractmethod
    def resolve_series_provider(self, provider_id: str) -> SeriesProvider:
        """Return a series-capable provider or raise a controlled provider error."""
        ...

    @abstractmethod
    def resolve_capability_provider(self, provider_id: str) -> CapabilityProvider:
        """Return the provider's runtime capability declaration without secrets."""
        ...
