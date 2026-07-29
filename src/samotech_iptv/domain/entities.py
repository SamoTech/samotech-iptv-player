"""Compatibility shim — Phase A import surface.

All public names re-exported from the new ``entities/`` package.
This module will be removed in a future major version.

.. deprecated::
    Import directly from ``samotech_iptv.domain.entities.<module>``
    or from ``samotech_iptv.domain.entities`` (the package).
"""
from samotech_iptv.domain.entities import (  # noqa: F401
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

__all__ = [
    "Channel", "Category", "Playlist", "Movie", "Series",
    "Episode", "Stream", "Provider", "EPGEntry", "Favorite", "History",
]
