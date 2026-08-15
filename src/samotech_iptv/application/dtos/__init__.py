"""DTOs package — re-exports all request/response transfer objects.

Usage (unchanged from Phase A)::

    from samotech_iptv.application.dtos import ChannelDTO, AuthenticateRequest

Or directly::

    from samotech_iptv.application.dtos.channels import ChannelDTO
"""

from samotech_iptv.application.dtos.auth import (
    AuthenticateRequest,
    AuthenticateResponse,
)
from samotech_iptv.application.dtos.categories import (
    CategoryDTO,
    LoadCategoriesRequest,
    LoadCategoriesResponse,
)
from samotech_iptv.application.dtos.channels import (
    ChannelDTO,
    LoadChannelsRequest,
    LoadChannelsResponse,
    SearchRegisteredChannelsRequest,
)
from samotech_iptv.application.dtos.content import (
    BrowseContentRequest,
    BrowseContentResponse,
    ContentItemDTO,
    ContentType,
)
from samotech_iptv.application.dtos.epg import (
    EPGEntryDTO,
    LoadEPGRequest,
    LoadEPGResponse,
    LoadRegisteredEPGRequest,
)
from samotech_iptv.application.dtos.favorites import (
    FavoriteDTO,
    ListFavoritesResponse,
    RemoveFavoriteResponse,
    SaveFavoriteRequest,
    SaveFavoriteResponse,
    SearchChannelsRequest,
    SearchChannelsResponse,
)
from samotech_iptv.application.dtos.history import (
    ClearHistoryResponse,
    HistoryItemDTO,
    LoadHistoryRequest,
    LoadHistoryResponse,
    RecordHistoryRequest,
    RecordHistoryResponse,
)
from samotech_iptv.application.dtos.playback import (
    PlaybackAttempt,
    PlaybackOutcome,
    PlaybackResult,
    PlaybackTarget,
)
from samotech_iptv.application.dtos.provider import (
    ProviderCapabilities,
    ProviderMetadata,
)
from samotech_iptv.application.dtos.provider_registration import (
    RegisterXtreamProviderRequest,
    RegisterXtreamProviderResponse,
)
from samotech_iptv.application.dtos.stream import (
    ResolveStreamRequest,
    ResolveStreamResponse,
)
from samotech_iptv.application.dtos.xmltv import (
    ConfigureXMLTVBindingRequest,
    ConfigureXMLTVBindingResponse,
    RefreshXMLTVGuideRequest,
    RefreshXMLTVGuideResponse,
    XMLTVChannelMappingRequest,
)

__all__ = [
    "ProviderMetadata",
    "ProviderCapabilities",
    "RegisterXtreamProviderRequest",
    "RegisterXtreamProviderResponse",
    "AuthenticateRequest",
    "AuthenticateResponse",
    "ChannelDTO",
    "LoadChannelsRequest",
    "LoadChannelsResponse",
    "SearchRegisteredChannelsRequest",
    "ContentType",
    "ContentItemDTO",
    "BrowseContentRequest",
    "BrowseContentResponse",
    "PlaybackTarget",
    "PlaybackAttempt",
    "PlaybackOutcome",
    "PlaybackResult",
    "CategoryDTO",
    "LoadCategoriesRequest",
    "LoadCategoriesResponse",
    "EPGEntryDTO",
    "LoadEPGRequest",
    "LoadEPGResponse",
    "LoadRegisteredEPGRequest",
    "ResolveStreamRequest",
    "ResolveStreamResponse",
    "ClearHistoryResponse",
    "HistoryItemDTO",
    "LoadHistoryRequest",
    "LoadHistoryResponse",
    "RecordHistoryRequest",
    "RecordHistoryResponse",
    "FavoriteDTO",
    "ListFavoritesResponse",
    "RemoveFavoriteResponse",
    "SaveFavoriteRequest",
    "SaveFavoriteResponse",
    "SearchChannelsRequest",
    "SearchChannelsResponse",
    "XMLTVChannelMappingRequest",
    "ConfigureXMLTVBindingRequest",
    "ConfigureXMLTVBindingResponse",
    "RefreshXMLTVGuideRequest",
    "RefreshXMLTVGuideResponse",
]
