"""Search channels through one registered provider's search capability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import (
    ChannelDTO,
    SearchChannelsResponse,
    SearchRegisteredChannelsRequest,
)
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort

__all__ = ["SearchRegisteredChannels"]

_LOG = get_logger("use_cases.search_registered_channels")


class SearchRegisteredChannels:
    """Resolve a registered provider and return its safe matching channel DTOs."""

    def __init__(self, provider_resolver: ProviderResolverPort) -> None:
        self._provider_resolver = provider_resolver

    async def execute(self, request: SearchRegisteredChannelsRequest) -> SearchChannelsResponse:
        """Search within the requested provider without exposing credentials or URLs."""
        _LOG.info(
            "Searching registered provider id=%s with limit=%d",
            request.provider_id,
            request.limit,
        )
        provider = self._provider_resolver.resolve_search_provider(request.provider_id)
        channels = await provider.search_channels(request.query, limit=request.limit)
        dtos = [
            ChannelDTO(
                id=str(channel.id),
                name=channel.name,
                provider_id=str(channel.provider_id),
                stream_id=str(channel.stream_id),
                category_id=channel.category_id,
                logo_url=str(channel.logo_url) if channel.logo_url else None,
                number=channel.number,
            )
            for channel in channels
        ]
        return SearchChannelsResponse(channels=dtos, total=len(dtos))
