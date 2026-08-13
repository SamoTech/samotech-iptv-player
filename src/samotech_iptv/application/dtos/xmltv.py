"""Safe application DTOs for local XMLTV source binding and refresh."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.epg import EPGEntryDTO

__all__ = [
    "ConfigureXMLTVBindingRequest",
    "ConfigureXMLTVBindingResponse",
    "RefreshXMLTVGuideRequest",
    "RefreshXMLTVGuideResponse",
    "XMLTVChannelMappingRequest",
]


@dataclass(frozen=True)
class XMLTVChannelMappingRequest:
    """One explicit XMLTV source-channel to canonical-channel association."""

    source_channel_id: str
    channel_id: str


@dataclass(frozen=True)
class ConfigureXMLTVBindingRequest:
    """Configure one provider's local XMLTV source and explicit mappings."""

    provider_id: str
    source: str
    mappings: Sequence[XMLTVChannelMappingRequest]


@dataclass(frozen=True)
class ConfigureXMLTVBindingResponse:
    """Generic configuration outcome with no source details."""

    success: bool
    error: str | None = None


@dataclass(frozen=True)
class RefreshXMLTVGuideRequest:
    """Refresh the currently configured local XMLTV guide for one provider."""

    provider_id: str
    limit: int = 48


@dataclass(frozen=True)
class RefreshXMLTVGuideResponse:
    """Bounded presentation-safe schedule entries or a generic refresh failure."""

    entries: Sequence[EPGEntryDTO] = field(default_factory=list)
    error: str | None = None
