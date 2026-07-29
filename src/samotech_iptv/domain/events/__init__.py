"""Domain events package — re-exports all event types.

Usage (unchanged from Phase A)::

    from samotech_iptv.domain.events import ProviderAuthenticatedEvent

Or directly::

    from samotech_iptv.domain.events.provider_events import ProviderAuthenticatedEvent
"""
from samotech_iptv.domain.events.provider_events import (
    ProviderAuthenticatedEvent,
    ProviderRefreshFailedEvent,
)
from samotech_iptv.domain.events.playback_events import (
    StreamResolvedEvent,
    HistoryRecordedEvent,
)
from samotech_iptv.domain.events.library_events import (
    ChannelsLoadedEvent,
    FavoriteSavedEvent,
)

__all__ = [
    "ProviderAuthenticatedEvent",
    "ProviderRefreshFailedEvent",
    "StreamResolvedEvent",
    "HistoryRecordedEvent",
    "ChannelsLoadedEvent",
    "FavoriteSavedEvent",
]
