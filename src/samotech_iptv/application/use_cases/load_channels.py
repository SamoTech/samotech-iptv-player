"""LoadChannels use-case."""
from __future__ import annotations

from samotech_iptv.application.dtos import (
    ChannelDTO,
    LoadChannelsRequest,
    LoadChannelsResponse,
)
from samotech_iptv.application.ports import ProviderPort
from samotech_iptv.core.logging import get_logger

_log = get_logger("use_cases.load_channels")


class LoadChannels:
    """Fetch all channels for a provider and return DTOs."""

    def __init__(self, provider: ProviderPort) -> None:
        self._provider = provider

    async def execute(self, request: LoadChannelsRequest) -> LoadChannelsResponse:
        _log.info("Loading channels for provider %s", request.provider_id)
        try:
            channels = await self._provider.load_channels()
        except Exception as exc:  # noqa: BLE001
            _log.error("LoadChannels error: %s", exc)
            return LoadChannelsResponse(error=str(exc))
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
            if request.category_id is None or ch.category_id == request.category_id
        ]
        return LoadChannelsResponse(channels=dtos, total=len(dtos))
