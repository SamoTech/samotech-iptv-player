"""Bounded local XMLTV refresh service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.ports.xmltv_guide_port import XMLTVGuidePort
from samotech_iptv.infrastructure.parsing.xmltv_parser import XMLTVParser

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding
    from samotech_iptv.infrastructure.parsing.xmltv_source_loader import XMLTVSourceLoaderPort

__all__ = ["XMLTVGuideService"]


class XMLTVGuideService(XMLTVGuidePort):
    """Refresh canonical EPG entries from one configured local XMLTV source."""

    def __init__(
        self,
        source_loader: XMLTVSourceLoaderPort,
        parser: XMLTVParser | None = None,
    ) -> None:
        self._source_loader = source_loader
        self._parser = parser or XMLTVParser()

    async def refresh(self, binding: XMLTVBinding) -> Sequence[EPGEntry]:
        """Load bounded source text and parse only explicitly mapped programmes."""
        text = await self._source_loader.load(binding.source)
        return self._parser.parse(text, binding.channel_mapping)
