"""Load EPG entries through a registered provider capability boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import EPGEntryDTO, LoadEPGResponse, LoadRegisteredEPGRequest
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects import ChannelId

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort

__all__ = ["LoadRegisteredEPG"]

_LOG = get_logger("use_cases.load_registered_epg")
_SAFE_LOAD_FAILURE = "Unable to load EPG for the selected channel"


class LoadRegisteredEPG:
    """Resolve a registered provider and return EPG data without provider secrets."""

    def __init__(self, provider_resolver: ProviderResolverPort) -> None:
        self._provider_resolver = provider_resolver

    async def execute(self, request: LoadRegisteredEPGRequest) -> LoadEPGResponse:
        """Load a bounded collection of presentation-safe programme entries."""
        _LOG.info("Loading EPG for provider id=%s", request.provider_id)
        try:
            provider = self._provider_resolver.resolve_epg_provider(request.provider_id)
            entries = await provider.load_epg(ChannelId(request.channel_id))
        except Exception:  # noqa: BLE001
            _LOG.exception("Unable to load EPG for registered provider id=%s", request.provider_id)
            return LoadEPGResponse(error=_SAFE_LOAD_FAILURE)

        limit = max(0, min(request.limit, 500))
        return LoadEPGResponse(
            entries=[
                EPGEntryDTO(
                    id=entry.id,
                    channel_id=str(entry.channel_id),
                    title=entry.title,
                    start=entry.start.isoformat(),
                    end=entry.end.isoformat(),
                    description=entry.description,
                    category=entry.category,
                )
                for entry in entries[:limit]
            ]
        )
