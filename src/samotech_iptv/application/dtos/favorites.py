"""Favorites and search DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.channels import ChannelDTO

__all__ = [
    "SaveFavoriteRequest",
    "SaveFavoriteResponse",
    "FavoriteDTO",
    "ListFavoritesResponse",
    "RemoveFavoriteResponse",
    "SearchChannelsRequest",
    "SearchChannelsResponse",
]


@dataclass(frozen=True)
class SaveFavoriteRequest:
    item_id: str
    item_type: str
    provider_id: str | None = None


@dataclass(frozen=True)
class SaveFavoriteResponse:
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class FavoriteDTO:
    id: str
    item_id: str
    item_type: str
    added_at: str
    provider_id: str | None = None


@dataclass(frozen=True)
class ListFavoritesResponse:
    favorites: Sequence[FavoriteDTO] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class RemoveFavoriteResponse:
    removed: bool
    error: str | None = None


@dataclass(frozen=True)
class SearchChannelsRequest:
    query: str
    limit: int = 100


@dataclass(frozen=True)
class SearchChannelsResponse:
    channels: Sequence[ChannelDTO] = field(default_factory=list)
    total: int = 0
