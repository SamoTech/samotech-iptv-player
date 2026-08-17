"""LoadEPG use-case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import EPGEntryDTO, LoadEPGRequest, LoadEPGResponse
from samotech_iptv.core.diagnostics import log_exception
from samotech_iptv.core.error_taxonomy import safe_user_message
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects import ChannelId

if TYPE_CHECKING:
    from samotech_iptv.application.ports import ProviderPort

_log = get_logger("use_cases.load_epg")


class LoadEPG:
    """Fetch EPG entries for a channel via the provider."""

    def __init__(self, provider: ProviderPort) -> None:
        self._provider = provider

    async def execute(self, request: LoadEPGRequest) -> LoadEPGResponse:
        _log.info("Loading EPG for channel %s", request.channel_id)
        try:
            entries = await self._provider.load_epg(ChannelId(request.channel_id))
        except Exception as exc:  # noqa: BLE001
            log_exception(_log, "LoadEPG error", exc, channel_id=request.channel_id)
            return LoadEPGResponse(error=safe_user_message(exc, fallback="Unable to load EPG"))
        dtos = [
            EPGEntryDTO(
                id=e.id,
                channel_id=str(e.channel_id),
                title=e.title,
                start=e.start.isoformat(),
                end=e.end.isoformat(),
                description=e.description,
            )
            for e in entries[: request.limit]
        ]
        return LoadEPGResponse(entries=dtos)
