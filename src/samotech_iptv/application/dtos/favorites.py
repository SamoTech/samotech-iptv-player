"""Favorites and search DTOs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from samotech_iptv.application.dtos.channels import ChannelDTO

__all__ = [
    "SaveFavoriteRequest",
    "SaveFavoriteResponse",
    "SearchChannelsRequest",
    "SearchChannelsResponse",
]


@dataclass(frozen=True)
class SaveFavoriteRequest:
    item_id: str
    item_type: str


@dataclass(frozen=True)
class SaveFavoriteResponse:
    success: bool
    error: Optional[str] = None


@dataclass(frozen=True)
class SearchChannelsRequest:
    query: str
    limit: int = 100


@dataclass(frozen=True)
class SearchChannelsResponse:
    channels: Sequence[ChannelDTO] = field(default_factory=list)
    total: int = 0
