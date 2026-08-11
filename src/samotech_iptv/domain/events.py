"""Compatibility shim — Phase A import surface.

All public names re-exported from the new ``events/`` package.

.. deprecated::
    Import directly from ``samotech_iptv.domain.events.<module>``
    or from ``samotech_iptv.domain.events`` (the package).
"""

from samotech_iptv.domain.events import (  # noqa: F401
    ChannelsLoadedEvent,
    FavoriteSavedEvent,
    HistoryRecordedEvent,
    ProviderAuthenticatedEvent,
    ProviderRefreshFailedEvent,
    StreamResolvedEvent,
)

__all__ = [
    "ProviderAuthenticatedEvent",
    "ProviderRefreshFailedEvent",
    "ChannelsLoadedEvent",
    "StreamResolvedEvent",
    "FavoriteSavedEvent",
    "HistoryRecordedEvent",
]
