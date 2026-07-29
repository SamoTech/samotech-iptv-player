"""Domain layer — pure business model.

Contains:
- Entities (immutable dataclasses)
- Value objects
- Repository *interfaces* (ABCs)

Allowed dependencies: ``samotech_iptv.core`` and stdlib only.
Forbidden: application, infrastructure, presentation, providers, aiohttp, SQLite.
"""

from samotech_iptv.domain.entities import (
    Channel,
    Category,
    Playlist,
    Movie,
    Series,
    Episode,
    Stream,
    Provider,
    EPGEntry,
    Favorite,
    History,
)
from samotech_iptv.domain.value_objects import (
    ProviderId,
    ChannelId,
    StreamId,
    Credential,
    URL,
)

__all__ = [
    # Entities
    "Channel",
    "Category",
    "Playlist",
    "Movie",
    "Series",
    "Episode",
    "Stream",
    "Provider",
    "EPGEntry",
    "Favorite",
    "History",
    # Value objects
    "ProviderId",
    "ChannelId",
    "StreamId",
    "Credential",
    "URL",
]
