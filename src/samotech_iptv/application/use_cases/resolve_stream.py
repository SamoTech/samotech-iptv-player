"""ResolveStream use-case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import ResolveStreamRequest, ResolveStreamResponse
from samotech_iptv.core.error_taxonomy import safe_user_message
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects import ChannelId

if TYPE_CHECKING:
    from samotech_iptv.application.ports import ProviderPort

_log = get_logger("use_cases.resolve_stream")


class ResolveStream:
    """Resolve a playable URL for a given channel."""

    def __init__(self, provider: ProviderPort) -> None:
        self._provider = provider

    async def execute(self, request: ResolveStreamRequest) -> ResolveStreamResponse:
        _log.info("Resolving stream for channel %s", request.channel_id)
        try:
            url = await self._provider.resolve_stream(ChannelId(request.channel_id))
        except Exception as exc:  # noqa: BLE001
            _log.error("ResolveStream error: %s", exc)
            return ResolveStreamResponse(
                error=safe_user_message(exc, fallback="Unable to resolve stream")
            )
        return ResolveStreamResponse(url=str(url))
