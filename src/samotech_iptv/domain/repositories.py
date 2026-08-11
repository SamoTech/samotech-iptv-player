"""Compatibility shim — Phase A import surface.

All public names re-exported from the new ``repositories/`` package.

.. deprecated::
    Import directly from ``samotech_iptv.domain.repositories.<module>``
    or from ``samotech_iptv.domain.repositories`` (the package).
"""
from samotech_iptv.domain.repositories import (  # noqa: F401
    ChannelRepository,
    EPGRepository,
    FavoriteRepository,
    HistoryRepository,
    PlaylistRepository,
    ProviderRepository,
)

__all__ = [
    "ChannelRepository", "PlaylistRepository", "ProviderRepository",
    "EPGRepository", "HistoryRepository", "FavoriteRepository",
]
