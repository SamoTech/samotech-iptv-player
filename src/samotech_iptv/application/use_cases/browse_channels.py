"""Load a registered provider's channel catalogue through application boundaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import LoadChannelsRequest, LoadChannelsResponse
from samotech_iptv.application.use_cases.load_channels import LoadChannels
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort

__all__ = ["BrowseChannels"]

_LOG = get_logger("use_cases.browse_channels")


class BrowseChannels:
    """Resolve a registered provider and return its safe channel DTO catalogue."""

    def __init__(self, provider_resolver: ProviderResolverPort) -> None:
        self._provider_resolver = provider_resolver

    async def execute(self, request: LoadChannelsRequest) -> LoadChannelsResponse:
        """Resolve the requested provider before delegating to the channel loader."""
        try:
            provider = self._provider_resolver.resolve_catalog_provider(request.provider_id)
        except Exception as exc:  # noqa: BLE001
            _LOG.error("Unable to resolve channel provider id=%s: %s", request.provider_id, exc)
            return LoadChannelsResponse(error=str(exc))
        return await LoadChannels(provider).execute(request)
