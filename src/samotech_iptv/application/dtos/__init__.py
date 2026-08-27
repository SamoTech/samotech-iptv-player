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
    LoadMovieDetailsRequest,
    LoadMovieDetailsResponse,
)
from samotech_iptv.application.dtos.discovery import (
    EpisodeDTO,
    LoadSeasonEpisodesRequest,
    LoadSeasonEpisodesResponse,
    LoadSeriesSeasonsRequest,
    LoadSeriesSeasonsResponse,
    SeasonDTO,
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
    RemoveHistoryResponse,
)
from samotech_iptv.application.dtos.playback import (
    PlaybackAttempt,
    PlaybackOutcome,
    PlaybackResource,
    PlaybackResult,
    PlaybackTarget,
    ResolvedPlayback,
    TransportHeader,
    TransportMetadata,
)
from samotech_iptv.application.dtos.player import (
    AudioTrack,
    PlaybackContext,
    PlaybackState,
    PlayerCapabilities,
    PlayerDiagnostics,
    SubtitleTrack,
)
from samotech_iptv.application.dtos.provider import (
    ProviderCapabilities,
    ProviderHealth,
    ProviderHealthStatus,
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
    "AudioTrack",
    "PlaybackContext",
    "PlaybackState",
    "PlayerCapabilities",
    "PlayerDiagnostics",
    "ProviderMetadata",
    "ProviderHealth",
    "ProviderHealthStatus",
    "SubtitleTrack",
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
    "LoadMovieDetailsRequest",
    "LoadMovieDetailsResponse",
    "SeasonDTO",
    "EpisodeDTO",
    "LoadSeriesSeasonsRequest",
    "LoadSeriesSeasonsResponse",
    "LoadSeasonEpisodesRequest",
    "LoadSeasonEpisodesResponse",
    "PlaybackResource",
    "PlaybackTarget",
    "ResolvedPlayback",
    "TransportHeader",
    "TransportMetadata",
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
    "RemoveHistoryResponse",
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
