"""Expose safe runtime provider capability declarations to presentation code."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider import ProviderCapabilities
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_content_resolver_port import (
        ProviderContentResolverPort,
    )

__all__ = ["LoadProviderCapabilities"]


class LoadProviderCapabilities:
    """Map a registered provider's executable capability set into a safe summary."""

    def __init__(self, provider_resolver: ProviderContentResolverPort) -> None:
        self._provider_resolver = provider_resolver

    def execute(self, provider_id: str) -> ProviderCapabilities:
        """Return only capabilities exposed by the constructed registered provider."""
        try:
            capabilities = self._provider_resolver.resolve_capability_provider(
                provider_id
            ).supported_capabilities()
        except ProviderError:
            return ProviderCapabilities()
        return ProviderCapabilities(
            live_tv=ProviderCapability.LIVE in capabilities,
            vod_movies=ProviderCapability.VOD in capabilities,
            vod_series=ProviderCapability.SERIES in capabilities,
            epg=ProviderCapability.EPG in capabilities,
            timeshift=ProviderCapability.CATCHUP in capabilities,
            catchup=ProviderCapability.CATCHUP in capabilities,
        )
