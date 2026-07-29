"""Use-case classes — application business logic.

Each use-case class has a single ``async def execute(request)`` method.
Use-cases depend only on port interfaces and domain objects.
"""

from samotech_iptv.application.use_cases.authenticate_provider import AuthenticateProvider
from samotech_iptv.application.use_cases.load_channels import LoadChannels
from samotech_iptv.application.use_cases.load_categories import LoadCategories
from samotech_iptv.application.use_cases.load_epg import LoadEPG
from samotech_iptv.application.use_cases.resolve_stream import ResolveStream
from samotech_iptv.application.use_cases.search_channels import SearchChannels
from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
from samotech_iptv.application.use_cases.load_history import LoadHistory
from samotech_iptv.application.use_cases.refresh_provider import RefreshProvider

__all__ = [
    "AuthenticateProvider",
    "LoadChannels",
    "LoadCategories",
    "LoadEPG",
    "ResolveStream",
    "SearchChannels",
    "SaveFavorite",
    "LoadHistory",
    "RefreshProvider",
]
