"""Domain entities package — re-exports every entity for a flat import surface.

Usage (unchanged from Phase A)::

    from samotech_iptv.domain.entities import Channel, EPGEntry

Or directly from the sub-module::

    from samotech_iptv.domain.entities.channel import Channel
"""

from samotech_iptv.domain.entities.account_info import AccountInfo
from samotech_iptv.domain.entities.catchup_event import CatchupEvent
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.entities.episode import Episode
from samotech_iptv.domain.entities.favorite import Favorite
from samotech_iptv.domain.entities.history import History
from samotech_iptv.domain.entities.movie import Movie
from samotech_iptv.domain.entities.playlist import Playlist
from samotech_iptv.domain.entities.provider import Provider
from samotech_iptv.domain.entities.provider_session import ProviderSession
from samotech_iptv.domain.entities.season import Season
from samotech_iptv.domain.entities.series import Series
from samotech_iptv.domain.entities.server_info import ServerInfo
from samotech_iptv.domain.entities.stream import Stream
from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding, XMLTVChannelMapping

__all__ = [
    "AccountInfo",
    "CatchupEvent",
    "Channel",
    "Category",
    "Playlist",
    "Movie",
    "Series",
    "Season",
    "Episode",
    "Stream",
    "Provider",
    "ProviderSession",
    "ServerInfo",
    "EPGEntry",
    "Favorite",
    "History",
    "XMLTVBinding",
    "XMLTVChannelMapping",
]
