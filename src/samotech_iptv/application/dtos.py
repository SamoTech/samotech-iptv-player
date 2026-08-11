"""Compatibility shim — Phase A import surface for application DTOs.

All public names re-exported from the new ``dtos/`` package.

.. deprecated::
    Import directly from ``samotech_iptv.application.dtos.<module>``
    or from ``samotech_iptv.application.dtos`` (the package).
"""
from samotech_iptv.application.dtos import (  # noqa: F401
    AuthenticateRequest,
    AuthenticateResponse,
    CategoryDTO,
    ChannelDTO,
    EPGEntryDTO,
    HistoryItemDTO,
    LoadCategoriesRequest,
    LoadCategoriesResponse,
    LoadChannelsRequest,
    LoadChannelsResponse,
    LoadEPGRequest,
    LoadEPGResponse,
    LoadHistoryRequest,
    LoadHistoryResponse,
    ProviderCapabilities,
    ProviderMetadata,
    ResolveStreamRequest,
    ResolveStreamResponse,
    SaveFavoriteRequest,
    SaveFavoriteResponse,
    SearchChannelsRequest,
    SearchChannelsResponse,
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
