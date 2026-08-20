"""Expose safe runtime provider capability declarations to presentation code."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider import (
    ProviderCapabilities,
    ProviderCapabilityState,
    ProviderCapabilityTruth,
)
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
            return ProviderCapabilities(
                truth=ProviderCapabilityTruth(
                    live_tv=ProviderCapabilityState.NOT_AVAILABLE,
                    vod_movies=ProviderCapabilityState.NOT_AVAILABLE,
                    vod_series=ProviderCapabilityState.NOT_AVAILABLE,
                    epg=ProviderCapabilityState.NOT_AVAILABLE,
                    timeshift=ProviderCapabilityState.NOT_AVAILABLE,
                    catchup=ProviderCapabilityState.NOT_AVAILABLE,
                )
            )
        live = ProviderCapability.LIVE in capabilities
        vod = ProviderCapability.VOD in capabilities
        series = ProviderCapability.SERIES in capabilities
        epg = ProviderCapability.EPG in capabilities
        catchup = ProviderCapability.CATCHUP in capabilities
        return ProviderCapabilities(
            live_tv=live,
            vod_movies=vod,
            vod_series=series,
            epg=epg,
            timeshift=catchup,
            catchup=catchup,
            truth=ProviderCapabilityTruth(
                live_tv=(
                    ProviderCapabilityState.SUPPORTED
                    if live
                    else ProviderCapabilityState.NOT_SUPPORTED
                ),
                vod_movies=(
                    ProviderCapabilityState.SUPPORTED
                    if vod
                    else ProviderCapabilityState.NOT_SUPPORTED
                ),
                vod_series=(
                    ProviderCapabilityState.SUPPORTED
                    if series
                    else ProviderCapabilityState.NOT_SUPPORTED
                ),
                epg=(
                    ProviderCapabilityState.SUPPORTED
                    if epg
                    else ProviderCapabilityState.NOT_SUPPORTED
                ),
                timeshift=(
                    ProviderCapabilityState.SUPPORTED
                    if catchup
                    else ProviderCapabilityState.NOT_SUPPORTED
                ),
                catchup=(
                    ProviderCapabilityState.SUPPORTED
                    if catchup
                    else ProviderCapabilityState.NOT_SUPPORTED
                ),
            ),
        )
