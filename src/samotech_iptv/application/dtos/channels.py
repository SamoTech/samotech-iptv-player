"""Channel DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "ChannelDTO",
    "LoadChannelsRequest",
    "LoadChannelsResponse",
    "SearchRegisteredChannelsRequest",
]


@dataclass(frozen=True)
class ChannelDTO:
    id: str
    name: str
    provider_id: str
    stream_id: str
    category_id: str | None = None
    logo_url: str | None = None
    number: int | None = None


@dataclass(frozen=True)
class LoadChannelsRequest:
    provider_id: str
    category_id: str | None = None


@dataclass(frozen=True)
class LoadChannelsResponse:
    channels: Sequence[ChannelDTO] = field(default_factory=list)
    total: int = 0
    error: str | None = None


@dataclass(frozen=True)
class SearchRegisteredChannelsRequest:
    """Request a bounded text search from one registered provider."""

    provider_id: str
    query: str
    limit: int = 100
