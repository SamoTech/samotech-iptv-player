"""Library (catalogue) domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from samotech_iptv.core.events import DomainEvent
from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["ChannelsLoadedEvent", "FavoriteSavedEvent"]


@dataclass(frozen=True)
class ChannelsLoadedEvent(DomainEvent):
    """Raised after a full channel list has been loaded from a provider."""

    event_name: ClassVar[str] = "channels.loaded"
    provider_id: ProviderId = ProviderId("unknown")
    count: int = 0


@dataclass(frozen=True)
class FavoriteSavedEvent(DomainEvent):
    """Raised after a favourite has been persisted."""

    event_name: ClassVar[str] = "favorite.saved"
    item_id: str = ""
