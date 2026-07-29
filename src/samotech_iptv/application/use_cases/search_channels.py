"""SearchChannels use-case."""
from __future__ import annotations

from samotech_iptv.application.dtos import (
    ChannelDTO,
    SearchChannelsRequest,
    SearchChannelsResponse,
)
from samotech_iptv.domain.repositories import ChannelRepository
from samotech_iptv.core.logging import get_logger

_log = get_logger("use_cases.search_channels")


class SearchChannels:
    """Full-text search over the local channel index."""

    def __init__(self, repository: ChannelRepository) -> None:
        self._repo = repository

    async def execute(self, request: SearchChannelsRequest) -> SearchChannelsResponse:
        _log.info("Searching channels: %r (limit=%d)", request.query, request.limit)
        channels = await self._repo.search(request.query, limit=request.limit)
        dtos = [
            ChannelDTO(
                id=str(ch.id),
                name=ch.name,
                provider_id=str(ch.provider_id),
                stream_id=str(ch.stream_id),
                category_id=ch.category_id,
                logo_url=str(ch.logo_url) if ch.logo_url else None,
                number=ch.number,
            )
            for ch in channels
        ]
        return SearchChannelsResponse(channels=dtos, total=len(dtos))
