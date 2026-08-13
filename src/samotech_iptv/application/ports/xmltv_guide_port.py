"""Application boundary for bounded XMLTV guide refresh."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding

__all__ = ["XMLTVGuidePort"]


class XMLTVGuidePort(ABC):
    """Load canonical programme entries for a configured non-secret XMLTV binding."""

    @abstractmethod
    async def refresh(self, binding: XMLTVBinding) -> Sequence[EPGEntry]:
        """Return bounded canonical entries or raise a source/parsing failure."""
