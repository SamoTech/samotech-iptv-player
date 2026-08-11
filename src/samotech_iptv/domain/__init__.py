"""Domain layer — pure business model.

Contains:
- Entities (immutable dataclasses) in ``entities/``
- Value objects in ``value_objects/``
- Repository *interfaces* (ABCs) in ``repositories/``
- Domain events in ``events/``

Allowed dependencies: ``samotech_iptv.core`` and stdlib only.
Forbidden: application, infrastructure, presentation, providers.
"""
from samotech_iptv.domain.entities import (
    Category,
    Channel,
    EPGEntry,
    Episode,
    Favorite,
    History,
    Movie,
    Playlist,
    Provider,
    Series,
    Stream,
)
from samotech_iptv.domain.value_objects import (
    URL,
    ChannelId,
    Credential,
    ProviderId,
    StreamId,
)

__all__ = [
    "Channel", "Category", "Playlist", "Movie", "Series",
    "Episode", "Stream", "Provider", "EPGEntry", "Favorite", "History",
    "ProviderId", "ChannelId", "StreamId", "Credential", "URL",
]
