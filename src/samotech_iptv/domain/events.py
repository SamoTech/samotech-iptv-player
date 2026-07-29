"""Domain-specific event types.

These events are published by application use-cases and consumed by
presentation-layer subscribers (UI refresh) or infrastructure listeners
(cache invalidation, logging).

All events are immutable dataclasses inheriting from ``DomainEvent``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from samotech_iptv.core.events import DomainEvent
from samotech_iptv.domain.value_objects import ChannelId, ProviderId

__all__ = [
    "ProviderAuthenticatedEvent",
    "ProviderRefreshFailedEvent",
    "ChannelsLoadedEvent",
    "StreamResolvedEvent",
    "FavoriteSavedEvent",
    "HistoryRecordedEvent",
]


@dataclass(frozen=True)
class ProviderAuthenticatedEvent(DomainEvent):
    event_name: ClassVar[str] = "provider.authenticated"
    provider_id: ProviderId = ProviderId("unknown")


@dataclass(frozen=True)
class ProviderRefreshFailedEvent(DomainEvent):
    event_name: ClassVar[str] = "provider.refresh_failed"
    provider_id: ProviderId = ProviderId("unknown")
    reason: str = ""


@dataclass(frozen=True)
class ChannelsLoadedEvent(DomainEvent):
    event_name: ClassVar[str] = "channels.loaded"
    provider_id: ProviderId = ProviderId("unknown")
    count: int = 0


@dataclass(frozen=True)
class StreamResolvedEvent(DomainEvent):
    event_name: ClassVar[str] = "stream.resolved"
    channel_id: ChannelId = ChannelId("unknown")


@dataclass(frozen=True)
class FavoriteSavedEvent(DomainEvent):
    event_name: ClassVar[str] = "favorite.saved"
    item_id: str = ""


@dataclass(frozen=True)
class HistoryRecordedEvent(DomainEvent):
    event_name: ClassVar[str] = "history.recorded"
    item_id: str = ""
