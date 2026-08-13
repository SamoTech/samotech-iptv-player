"""Refresh bounded programme entries from a configured local XMLTV binding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import (
    EPGEntryDTO,
    RefreshXMLTVGuideRequest,
    RefreshXMLTVGuideResponse,
)
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects.provider_id import ProviderId

if TYPE_CHECKING:
    from samotech_iptv.application.ports.xmltv_guide_port import XMLTVGuidePort
    from samotech_iptv.domain.repositories.xmltv_binding_repository import XMLTVBindingRepository

__all__ = ["RefreshXMLTVGuide"]

_LOG = get_logger(__name__)
_ERROR = "Unable to refresh XMLTV guide"


class RefreshXMLTVGuide:
    """Load one registered provider's configured local XMLTV schedule on demand."""

    def __init__(
        self,
        binding_repository: XMLTVBindingRepository,
        guide_service: XMLTVGuidePort,
    ) -> None:
        self._binding_repository = binding_repository
        self._guide_service = guide_service

    async def execute(self, request: RefreshXMLTVGuideRequest) -> RefreshXMLTVGuideResponse:
        """Return capped presentation-safe programme entries from the configured binding."""
        try:
            if request.limit <= 0:
                raise ValueError("XMLTV entry limit must be positive")
            binding = await self._binding_repository.load(ProviderId(request.provider_id))
            if binding is None:
                return RefreshXMLTVGuideResponse(error=_ERROR)
            entries = await self._guide_service.refresh(binding)
        except Exception:  # noqa: BLE001
            _LOG.error("Unable to refresh XMLTV guide")
            return RefreshXMLTVGuideResponse(error=_ERROR)
        return RefreshXMLTVGuideResponse(
            entries=[
                EPGEntryDTO(
                    id=entry.id,
                    channel_id=entry.channel_id.value,
                    title=entry.title,
                    start=entry.start.isoformat(),
                    end=entry.end.isoformat(),
                    description=None,
                )
                for entry in entries[: request.limit]
            ]
        )
