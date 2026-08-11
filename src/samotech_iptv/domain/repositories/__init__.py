"""Repository interfaces package — re-exports all abstract repository ABCs.

Usage (unchanged from Phase A)::

    from samotech_iptv.domain.repositories import ChannelRepository

Or directly::

    from samotech_iptv.domain.repositories.channel_repository import ChannelRepository
"""
from samotech_iptv.domain.repositories.channel_repository import ChannelRepository
from samotech_iptv.domain.repositories.epg_repository import EPGRepository
from samotech_iptv.domain.repositories.favorite_repository import FavoriteRepository
from samotech_iptv.domain.repositories.history_repository import HistoryRepository
from samotech_iptv.domain.repositories.playlist_repository import PlaylistRepository
from samotech_iptv.domain.repositories.provider_repository import ProviderRepository

__all__ = [
    "ChannelRepository",
    "PlaylistRepository",
    "ProviderRepository",
    "EPGRepository",
    "HistoryRepository",
    "FavoriteRepository",
]
