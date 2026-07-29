"""DTOs package — re-exports all request/response transfer objects.

Usage (unchanged from Phase A)::

    from samotech_iptv.application.dtos import ChannelDTO, AuthenticateRequest

Or directly::

    from samotech_iptv.application.dtos.channels import ChannelDTO
"""
from samotech_iptv.application.dtos.provider import ProviderMetadata, ProviderCapabilities
from samotech_iptv.application.dtos.auth import AuthenticateRequest, AuthenticateResponse
from samotech_iptv.application.dtos.channels import (
    ChannelDTO, LoadChannelsRequest, LoadChannelsResponse,
)
from samotech_iptv.application.dtos.categories import (
    CategoryDTO, LoadCategoriesRequest, LoadCategoriesResponse,
)
from samotech_iptv.application.dtos.epg import (
    EPGEntryDTO, LoadEPGRequest, LoadEPGResponse,
)
from samotech_iptv.application.dtos.stream import (
    ResolveStreamRequest, ResolveStreamResponse,
)
from samotech_iptv.application.dtos.history import (
    HistoryItemDTO, LoadHistoryRequest, LoadHistoryResponse,
)
from samotech_iptv.application.dtos.favorites import (
    SaveFavoriteRequest, SaveFavoriteResponse, SearchChannelsRequest, SearchChannelsResponse,
)

__all__ = [
    "ProviderMetadata", "ProviderCapabilities",
    "AuthenticateRequest", "AuthenticateResponse",
    "ChannelDTO", "LoadChannelsRequest", "LoadChannelsResponse",
    "CategoryDTO", "LoadCategoriesRequest", "LoadCategoriesResponse",
    "EPGEntryDTO", "LoadEPGRequest", "LoadEPGResponse",
    "ResolveStreamRequest", "ResolveStreamResponse",
    "HistoryItemDTO", "LoadHistoryRequest", "LoadHistoryResponse",
    "SaveFavoriteRequest", "SaveFavoriteResponse",
    "SearchChannelsRequest", "SearchChannelsResponse",
]
