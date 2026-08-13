"""LoadChannels use-case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import (
    ChannelDTO,
    LoadChannelsRequest,
    LoadChannelsResponse,
)
from samotech_iptv.core.diagnostics import DiagnosticTrace, log_exception, safe_label
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import CatalogProvider

_log = get_logger("use_cases.load_channels")


class LoadChannels:
    """Fetch all channels for a provider and return DTOs."""

    def __init__(self, provider: CatalogProvider) -> None:
        self._provider = provider

    async def execute(self, request: LoadChannelsRequest) -> LoadChannelsResponse:
        _log.info("Loading channels for provider %s", request.provider_id)
        trace = DiagnosticTrace(
            "LOAD_CHANNELS",
            str(request.provider_id),
            type(self._provider).__name__,
        )
        trace.start()
        try:
            with trace.stage("Provider resolution", provider=str(request.provider_id)):
                channels = await self._provider.load_channels()
        except Exception as exc:  # noqa: BLE001
            log_exception(
                _log,
                "LoadChannels error",
                exc,
                provider_id=request.provider_id,
            )
            trace.result(
                "FAIL",
                error_type=type(exc).__name__,
                error=safe_label(exc),
                records_received=0,
            )
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
        trace.result(
            "PASS",
            records_received=len(channels),
            records_translated=len(dtos),
            records_rejected=len(channels) - len(dtos),
        )
        return LoadChannelsResponse(channels=dtos, total=len(dtos))
