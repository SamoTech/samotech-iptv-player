"""Use-case classes — application business logic.

Each use-case class has a single ``async def execute(request)`` method.
Use-cases depend only on port interfaces and domain objects.
"""

from samotech_iptv.application.use_cases.authenticate_provider import (
    AuthenticateProvider,
)
from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
from samotech_iptv.application.use_cases.clear_history import ClearHistory
from samotech_iptv.application.use_cases.list_favorites import ListFavorites
from samotech_iptv.application.use_cases.load_categories import LoadCategories
from samotech_iptv.application.use_cases.load_channels import LoadChannels
from samotech_iptv.application.use_cases.load_epg import LoadEPG
from samotech_iptv.application.use_cases.load_history import LoadHistory
from samotech_iptv.application.use_cases.load_registered_epg import LoadRegisteredEPG
from samotech_iptv.application.use_cases.load_theme_preference import LoadThemePreference
from samotech_iptv.application.use_cases.play_channel import PlayChannel
from samotech_iptv.application.use_cases.play_registered_channel import PlayRegisteredChannel
from samotech_iptv.application.use_cases.record_history import RecordHistory
from samotech_iptv.application.use_cases.refresh_provider import RefreshProvider
from samotech_iptv.application.use_cases.register_xtream_provider import RegisterXtreamProvider
from samotech_iptv.application.use_cases.resolve_stream import ResolveStream
from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
from samotech_iptv.application.use_cases.save_theme_preference import SaveThemePreference
from samotech_iptv.application.use_cases.search_channels import SearchChannels
from samotech_iptv.application.use_cases.search_registered_channels import (
    SearchRegisteredChannels,
)
from samotech_iptv.application.use_cases.start_recording import StartRecording
from samotech_iptv.application.use_cases.stop_recording import StopRecording

__all__ = [
    "AuthenticateProvider",
    "BrowseChannels",
    "ClearHistory",
    "LoadChannels",
    "ListFavorites",
    "LoadCategories",
    "LoadEPG",
    "LoadRegisteredEPG",
    "LoadThemePreference",
    "ResolveStream",
    "PlayChannel",
    "PlayRegisteredChannel",
    "SearchChannels",
    "SearchRegisteredChannels",
    "StartRecording",
    "StopRecording",
    "SaveFavorite",
    "SaveThemePreference",
    "LoadHistory",
    "RecordHistory",
    "RefreshProvider",
    "RemoveFavorite",
    "RegisterXtreamProvider",
]
