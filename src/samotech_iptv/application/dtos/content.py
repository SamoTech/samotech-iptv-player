"""Content-family-aware DTOs for presentation catalogue views."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "BrowseContentRequest",
    "BrowseContentResponse",
    "ContentItemDTO",
    "ContentType",
    "LoadMovieDetailsRequest",
    "LoadMovieDetailsResponse",
]


class ContentType(StrEnum):
    """Canonical presentation content families without conflating domain entities."""

    LIVE = "live"
    MOVIE = "movie"
    SERIES = "series"
    EPISODE = "episode"


@dataclass(frozen=True)
class ContentItemDTO:
    """A safe, identity-preserving catalogue projection for non-live presentation views."""

    id: str
    provider_id: str
    content_type: ContentType
    title: str
    stream_id: str | None = None
    category_id: str | None = None
    poster_url: str | None = None
    year: int | None = None
    rating: float | None = None
    plot: str | None = None
    series_id: str | None = None
    season: int | None = None
    episode_number: int | None = None
    duration_seconds: int | None = None
    genre: str | None = None
    director: str | None = None
    cast: str | None = None
    country: str | None = None
    release_date: str | None = None
    backdrop_url: str | None = None
    container_extension: str | None = None
    season_count: int | None = None
    episode_count: int | None = None


@dataclass(frozen=True)
class BrowseContentRequest:
    """Request an explicit, provider-scoped non-live catalogue load."""

    provider_id: str
    content_type: ContentType


@dataclass(frozen=True)
class BrowseContentResponse:
    """Return a safe content projection while preserving unsupported/error semantics."""

    items: Sequence[ContentItemDTO] = field(default_factory=list)
    total: int = 0
    error: str | None = None
    unsupported: bool = False


@dataclass(frozen=True)
class LoadMovieDetailsRequest:
    """Request one safe provider-scoped VOD detail projection."""

    provider_id: str
    movie_id: str


@dataclass(frozen=True)
class LoadMovieDetailsResponse:
    """Return one detail projection without a resolved playback URL."""

    item: ContentItemDTO | None = None
    error: str | None = None
    unsupported: bool = False
