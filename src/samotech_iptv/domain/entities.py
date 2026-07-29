"""Domain entities — immutable dataclasses representing business objects.

No I/O.  No external libraries.  No business logic beyond invariant
validation in ``__post_init__``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Sequence

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects import ChannelId, ProviderId, StreamId, URL

__all__ = [
    "Channel",
    "Category",
    "Playlist",
    "Movie",
    "Series",
    "Episode",
    "Stream",
    "Provider",
    "EPGEntry",
    "Favorite",
    "History",
]


@dataclass(frozen=True)
class Category:
    """A grouping of channels or VOD content from a provider."""

    id: str
    name: str
    provider_id: ProviderId
    parent_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name", "Category name must not be blank")


@dataclass(frozen=True)
class Channel:
    """A live-TV channel available through a provider."""

    id: ChannelId
    name: str
    provider_id: ProviderId
    stream_id: StreamId
    category_id: Optional[str] = None
    logo_url: Optional[URL] = None
    epg_channel_id: Optional[str] = None
    number: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name", "Channel name must not be blank")


@dataclass(frozen=True)
class Stream:
    """A playable media stream URI with associated metadata."""

    id: StreamId
    url: URL
    container: str = "ts"  # e.g. ts, mp4, mkv
    codec: Optional[str] = None
    bitrate_kbps: Optional[int] = None
    is_encrypted: bool = False


@dataclass(frozen=True)
class EPGEntry:
    """A single Electronic Programme Guide entry."""

    id: str
    channel_id: ChannelId
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    category: Optional[str] = None

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValidationError("end", "EPG end time must be after start time")


@dataclass(frozen=True)
class Movie:
    """A VOD movie entry."""

    id: str
    title: str
    provider_id: ProviderId
    stream_id: StreamId
    category_id: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    poster_url: Optional[URL] = None
    plot: Optional[str] = None


@dataclass(frozen=True)
class Series:
    """A VOD series (collection of seasons/episodes)."""

    id: str
    title: str
    provider_id: ProviderId
    category_id: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    poster_url: Optional[URL] = None
    plot: Optional[str] = None


@dataclass(frozen=True)
class Episode:
    """A single episode belonging to a series."""

    id: str
    series_id: str
    title: str
    stream_id: StreamId
    season: int
    episode_number: int
    duration_seconds: Optional[int] = None
    plot: Optional[str] = None

    def __post_init__(self) -> None:
        if self.season < 1:
            raise ValidationError("season", "Season number must be >= 1")
        if self.episode_number < 1:
            raise ValidationError("episode_number", "Episode number must be >= 1")


@dataclass(frozen=True)
class Provider:
    """Metadata describing a registered content provider."""

    id: ProviderId
    name: str
    type: str  # e.g. "mag", "xtream", "m3u"
    base_url: URL
    is_active: bool = True
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name", "Provider name must not be blank")


@dataclass(frozen=True)
class Playlist:
    """A user-defined or provider-sourced ordered list of channels."""

    id: str
    name: str
    provider_id: ProviderId
    channel_ids: tuple[ChannelId, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name", "Playlist name must not be blank")


@dataclass(frozen=True)
class Favorite:
    """A channel or VOD item the user has marked as favourite."""

    id: str
    item_id: str
    item_type: str  # "channel" | "movie" | "series"
    added_at: datetime


@dataclass(frozen=True)
class History:
    """A single playback history record."""

    id: str
    item_id: str
    item_type: str  # "channel" | "movie" | "episode"
    watched_at: datetime
    duration_seconds: int = 0
    position_seconds: int = 0
