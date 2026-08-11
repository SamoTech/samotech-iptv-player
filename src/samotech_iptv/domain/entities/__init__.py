"""Domain entities package — re-exports every entity for a flat import surface.

Usage (unchanged from Phase A)::

    from samotech_iptv.domain.entities import Channel, EPGEntry

Or directly from the sub-module::

    from samotech_iptv.domain.entities.channel import Channel
"""
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.entities.episode import Episode
from samotech_iptv.domain.entities.favorite import Favorite
from samotech_iptv.domain.entities.history import History
from samotech_iptv.domain.entities.movie import Movie
from samotech_iptv.domain.entities.playlist import Playlist
from samotech_iptv.domain.entities.provider import Provider
from samotech_iptv.domain.entities.series import Series
from samotech_iptv.domain.entities.stream import Stream

__all__ = [
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
]
