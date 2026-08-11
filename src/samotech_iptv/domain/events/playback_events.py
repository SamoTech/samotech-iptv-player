"""Playback-related domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from samotech_iptv.core.events import DomainEvent
from samotech_iptv.domain.value_objects.channel_id import ChannelId

__all__ = ["StreamResolvedEvent", "HistoryRecordedEvent"]


@dataclass(frozen=True)
class StreamResolvedEvent(DomainEvent):
    """Raised when a stream URL has been successfully resolved."""

    event_name: ClassVar[str] = "stream.resolved"
    channel_id: ChannelId = ChannelId("unknown")


@dataclass(frozen=True)
class HistoryRecordedEvent(DomainEvent):
    """Raised after a playback history record is persisted."""

    event_name: ClassVar[str] = "history.recorded"
    item_id: str = ""
