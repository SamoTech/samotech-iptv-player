"""Data Transfer Objects — boundary objects between layers.

DTOs carry data across layer boundaries.  They are plain dataclasses
with no behaviour.  Domain entities must be mapped to DTOs before
being handed to the presentation layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

__all__ = [
    "ProviderMetadata",
    "ProviderCapabilities",
    "AuthenticateRequest",
    "AuthenticateResponse",
    "LoadChannelsRequest",
    "LoadChannelsResponse",
    "ChannelDTO",
    "LoadCategoriesRequest",
    "LoadCategoriesResponse",
    "CategoryDTO",
    "LoadEPGRequest",
    "LoadEPGResponse",
    "EPGEntryDTO",
    "ResolveStreamRequest",
    "ResolveStreamResponse",
    "SearchChannelsRequest",
    "SearchChannelsResponse",
    "SaveFavoriteRequest",
    "SaveFavoriteResponse",
    "LoadHistoryRequest",
    "LoadHistoryResponse",
    "HistoryItemDTO",
]


@dataclass(frozen=True)
class ProviderCapabilities:
    live_tv: bool = False
    vod_movies: bool = False
    vod_series: bool = False
    epg: bool = False
    timeshift: bool = False
    catchup: bool = False


@dataclass(frozen=True)
class ProviderMetadata:
    id: str
    name: str
    type: str
    base_url: str
    is_active: bool
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)


# ── Channel DTOs ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ChannelDTO:
    id: str
    name: str
    provider_id: str
    stream_id: str
    category_id: Optional[str] = None
    logo_url: Optional[str] = None
    number: Optional[int] = None


@dataclass(frozen=True)
class LoadChannelsRequest:
    provider_id: str
    category_id: Optional[str] = None


@dataclass(frozen=True)
class LoadChannelsResponse:
    channels: Sequence[ChannelDTO] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


# ── Category DTOs ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CategoryDTO:
    id: str
    name: str
    provider_id: str
    parent_id: Optional[str] = None


@dataclass(frozen=True)
class LoadCategoriesRequest:
    provider_id: str


@dataclass(frozen=True)
class LoadCategoriesResponse:
    categories: Sequence[CategoryDTO] = field(default_factory=list)
    error: Optional[str] = None


# ── Auth DTOs ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AuthenticateRequest:
    provider_id: str
    username: str
    password: str


@dataclass(frozen=True)
class AuthenticateResponse:
    success: bool
    provider_id: str
    error: Optional[str] = None


# ── EPG DTOs ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EPGEntryDTO:
    id: str
    channel_id: str
    title: str
    start: str  # ISO-8601
    end: str    # ISO-8601
    description: Optional[str] = None


@dataclass(frozen=True)
class LoadEPGRequest:
    channel_id: str
    limit: int = 48


@dataclass(frozen=True)
class LoadEPGResponse:
    entries: Sequence[EPGEntryDTO] = field(default_factory=list)
    error: Optional[str] = None


# ── Stream DTOs ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ResolveStreamRequest:
    channel_id: str
    provider_id: str


@dataclass(frozen=True)
class ResolveStreamResponse:
    url: Optional[str] = None
    error: Optional[str] = None


# ── Search DTOs ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SearchChannelsRequest:
    query: str
    limit: int = 100


@dataclass(frozen=True)
class SearchChannelsResponse:
    channels: Sequence[ChannelDTO] = field(default_factory=list)
    total: int = 0


# ── Favorite DTOs ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SaveFavoriteRequest:
    item_id: str
    item_type: str


@dataclass(frozen=True)
class SaveFavoriteResponse:
    success: bool
    error: Optional[str] = None


# ── History DTOs ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HistoryItemDTO:
    id: str
    item_id: str
    item_type: str
    watched_at: str  # ISO-8601
    duration_seconds: int = 0


@dataclass(frozen=True)
class LoadHistoryRequest:
    limit: int = 50


@dataclass(frozen=True)
class LoadHistoryResponse:
    items: Sequence[HistoryItemDTO] = field(default_factory=list)
    error: Optional[str] = None
